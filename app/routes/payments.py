from flask import Blueprint, request, jsonify
from app.services.pesapal import PesaPal
from app.database import SessionLocal
from app.models.payment import Payment, TransactionStatus
from app.models.job import Job, JobStatus
from app.models.institution import Institution
from app.models.professional import Professional
from app.models.user import UserRole
from app.middleware.auth import token_required, role_required
from datetime import datetime
import uuid

payments_blueprint = Blueprint("payments", __name__)

@payments_blueprint.post("/initiate")
@token_required
@role_required(UserRole.INSTITUTION)
def initiate_payment(current_user):
    db = SessionLocal()
    try:
        data = request.json
        gig_id = data.get('gig_id')
        
        if not gig_id:
            return jsonify({"error": "Gig ID is required"}), 400
        
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not institution:
            return jsonify({"error": "Institution profile not found"}), 404
        
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            return jsonify({"error": "Gig not found or unauthorized"}), 404
        
        if gig.status not in [JobStatus.ASSIGNED, JobStatus.COMPLETED]:
            return jsonify({"error": "Gig must be assigned or completed before payment"}), 400
        
        if not gig.assigned_professional_id:
            return jsonify({"error": "No professional assigned to this gig"}), 400
        
        existing_payment = db.query(Payment).filter(
            Payment.gig_id == gig.id,
            Payment.status == TransactionStatus.COMPLETED
        ).first()
        
        if existing_payment:
            return jsonify({"error": "Payment already completed for this gig"}), 400
        
        professional = db.query(Professional).filter(Professional.id == gig.assigned_professional_id).first()
        
        merchant_reference = f"QGIG-{uuid.uuid4().hex[:12].upper()}"
        
        payment = Payment(
            gig_id=gig.id,
            institution_id=institution.id,
            professional_id=professional.id,
            amount=gig.pay_amount,
            pesapal_merchant_reference=merchant_reference,
            status=TransactionStatus.PENDING
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        pesapal = PesaPal()
        
        try:
            response = pesapal.initiate_payment(
                amount=gig.pay_amount,
                email=current_user.email,
                phone=institution.phone or "0700000000",
                merchant_reference=merchant_reference
            )

            order_tracking_id = (
                response.get('order_tracking_id')
                or response.get('OrderTrackingId')
                or response.get('orderTrackingId')
                or response.get('OrderTrackingID')
            )
            redirect_url = (
                response.get('redirect_url')
                or response.get('RedirectURL')
                or response.get('redirectUrl')
            )

            if not order_tracking_id:
                raise Exception(f"Payment provider did not return order tracking id: {response}")

            payment.pesapal_order_tracking_id = order_tracking_id
            db.commit()
            
            return jsonify({
                "message": "Payment initiated successfully",
                "payment_id": payment.id,
                "redirect_url": redirect_url,
                "order_tracking_id": order_tracking_id
            }), 201
            
        except Exception as e:
            payment.status = TransactionStatus.FAILED
            db.commit()
            return jsonify({"error": f"Payment initiation failed: {str(e)}"}), 500
            
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@payments_blueprint.post("/webhook")
def webhook():
    db = SessionLocal()
    try:
        data = request.json
        order_tracking_id = data.get('OrderTrackingId')
        
        if not order_tracking_id:
            return jsonify({"status": "error", "message": "Missing OrderTrackingId"}), 400
        
        payment = db.query(Payment).filter(
            Payment.pesapal_order_tracking_id == order_tracking_id
        ).first()
        
        if not payment:
            return jsonify({"status": "error", "message": "Payment not found"}), 404
        
        pesapal = PesaPal()
        status_response = pesapal.get_transaction_status(order_tracking_id)
        
        payment_status = status_response.get('payment_status_description', '').lower()
        
        if payment_status == 'completed':
            payment.status = TransactionStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            payment.pesapal_transaction_id = status_response.get('transaction_id')
            payment.payment_method = status_response.get('payment_method')
            
            gig = db.query(Job).filter(Job.id == payment.gig_id).first()
            if gig:
                gig.status = JobStatus.COMPLETED
            
        elif payment_status == 'failed':
            payment.status = TransactionStatus.FAILED
        elif payment_status == 'cancelled':
            payment.status = TransactionStatus.CANCELLED
        
        payment.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({"status": "success", "message": "Webhook processed"}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

@payments_blueprint.get("/status/<int:payment_id>")
@token_required
def get_payment_status(current_user, payment_id):
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        professional = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        
        if not ((institution and payment.institution_id == institution.id) or 
                (professional and payment.professional_id == professional.id)):
            return jsonify({"error": "Unauthorized"}), 403
        
        return jsonify({
            "payment_id": payment.id,
            "amount": payment.amount,
            "status": payment.status.value,
            "created_at": payment.created_at.isoformat(),
            "completed_at": payment.completed_at.isoformat() if payment.completed_at else None,
            "gig_id": payment.gig_id
        }), 200
        
    finally:
        db.close()

@payments_blueprint.get("/my-payments")
@token_required
def get_my_payments(current_user):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        professional = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        
        if institution:
            payments = db.query(Payment).filter(Payment.institution_id == institution.id).all()
        elif professional:
            payments = db.query(Payment).filter(Payment.professional_id == professional.id).all()
        else:
            return jsonify({"payments": []}), 200
        
        return jsonify({
            "payments": [{
                "id": p.id,
                "amount": p.amount,
                "status": p.status.value,
                "gig_title": p.gig.title,
                "created_at": p.created_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None
            } for p in payments]
        }), 200
        
    finally:
        db.close()
