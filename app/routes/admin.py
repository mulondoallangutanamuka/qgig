from flask import Blueprint, request, jsonify, send_file
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.job import Job, JobStatus
from app.models.payment import Payment, TransactionStatus
from app.models.document import Document, DocumentStatus
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.rating import Rating
from app.middleware.auth import token_required, role_required
from sqlalchemy import func
from datetime import datetime
import os

admin_blueprint = Blueprint("admin", __name__)

@admin_blueprint.get("/metrics")
@token_required
@role_required(UserRole.ADMIN)
def get_system_metrics(current_user):
    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        total_professionals = db.query(Professional).count()
        total_institutions = db.query(Institution).count()
        
        total_gigs = db.query(Job).count()
        open_gigs = db.query(Job).filter(Job.status == JobStatus.OPEN).count()
        assigned_gigs = db.query(Job).filter(Job.status == JobStatus.ASSIGNED).count()
        completed_gigs = db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        
        total_payments = db.query(Payment).count()
        completed_payments = db.query(Payment).filter(Payment.status == TransactionStatus.COMPLETED).count()
        pending_payments = db.query(Payment).filter(Payment.status == TransactionStatus.PENDING).count()
        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        verified_professionals = db.query(Professional).join(User).join(Document).filter(
            Document.status == DocumentStatus.APPROVED
        ).distinct().count()
        
        pending_documents = db.query(Document).filter(Document.status == DocumentStatus.PENDING).count()
        
        avg_rating = db.query(func.avg(Rating.rating)).scalar() or 0
        
        return jsonify({
            "users": {
                "total": total_users,
                "professionals": total_professionals,
                "institutions": total_institutions
            },
            "gigs": {
                "total": total_gigs,
                "open": open_gigs,
                "assigned": assigned_gigs,
                "completed": completed_gigs
            },
            "payments": {
                "total": total_payments,
                "completed": completed_payments,
                "pending": pending_payments,
                "total_revenue": float(total_revenue)
            },
            "verification": {
                "verified_professionals": verified_professionals,
                "pending_documents": pending_documents
            },
            "ratings": {
                "average_rating": round(float(avg_rating), 2)
            }
        }), 200
        
    finally:
        db.close()

@admin_blueprint.get("/users")
@token_required
@role_required(UserRole.ADMIN)
def get_all_users(current_user):
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        return jsonify({
            "users": [{
                "id": u.id,
                "email": u.email,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat()
            } for u in users]
        }), 200
        
    finally:
        db.close()

@admin_blueprint.put("/users/<int:user_id>/suspend")
@token_required
@role_required(UserRole.ADMIN)
def suspend_user(current_user, user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if user.role == UserRole.ADMIN:
            return jsonify({"error": "Cannot suspend admin users"}), 403
        
        user.is_active = False
        db.commit()
        
        return jsonify({"message": f"User {user.email} suspended successfully"}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@admin_blueprint.put("/users/<int:user_id>/activate")
@token_required
@role_required(UserRole.ADMIN)
def activate_user(current_user, user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user.is_active = True
        db.commit()
        
        return jsonify({"message": f"User {user.email} activated successfully"}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@admin_blueprint.get("/documents/pending")
@token_required
@role_required(UserRole.ADMIN)
def get_pending_documents(current_user):
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(Document.status == DocumentStatus.PENDING).all()
        
        return jsonify({
            "documents": [{
                "id": d.id,
                "professional_id": d.professional_id,
                "document_type": d.document_type.value,
                "file_path": d.file_path,
                "uploaded_at": d.uploaded_at.isoformat()
            } for d in documents]
        }), 200
        
    finally:
        db.close()

@admin_blueprint.put("/documents/<int:doc_id>/approve")
@token_required
@role_required(UserRole.ADMIN)
def approve_document(current_user, doc_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            return jsonify({"error": "Document not found"}), 404
        
        document.status = DocumentStatus.APPROVED
        document.reviewed_at = datetime.utcnow()
        document.reviewed_by = current_user.id
        db.commit()
        
        return jsonify({"message": "Document approved successfully"}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@admin_blueprint.put("/documents/<int:doc_id>/reject")
@token_required
@role_required(UserRole.ADMIN)
def reject_document(current_user, doc_id):
    db = SessionLocal()
    try:
        data = request.json
        reason = data.get('reason', 'Document does not meet requirements')
        
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            return jsonify({"error": "Document not found"}), 404
        
        document.status = DocumentStatus.REJECTED
        document.reviewed_at = datetime.utcnow()
        document.reviewed_by = current_user.id
        db.commit()
        
        return jsonify({"message": f"Document rejected: {reason}"}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@admin_blueprint.get("/gigs/all")
@token_required
@role_required(UserRole.ADMIN)
def get_all_gigs(current_user):
    db = SessionLocal()
    try:
        gigs = db.query(Job).all()
        
        return jsonify({
            "gigs": [{
                "id": g.id,
                "title": g.title,
                "status": g.status.value,
                "institution_id": g.institution_id,
                "assigned_professional_id": g.assigned_professional_id,
                "pay_amount": g.pay_amount,
                "created_at": g.created_at.isoformat()
            } for g in gigs]
        }), 200
        
    finally:
        db.close()

@admin_blueprint.get("/payments/all")
@token_required
@role_required(UserRole.ADMIN)
def get_all_payments(current_user):
    db = SessionLocal()
    try:
        payments = db.query(Payment).all()
        
        return jsonify({
            "payments": [{
                "id": p.id,
                "gig_id": p.gig_id,
                "amount": p.amount,
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None
            } for p in payments]
        }), 200
        
    finally:
        db.close()

@admin_blueprint.get("/documents/all")
@token_required
@role_required(UserRole.ADMIN)
def get_all_documents(current_user):
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        
        return jsonify({
            "documents": [{
                "id": d.id,
                "user_id": d.user_id,
                "professional_id": d.professional_id,
                "document_type": d.document_type.value,
                "file_name": d.file_name,
                "file_path": d.file_path,
                "status": d.status.value,
                "uploaded_at": d.uploaded_at.isoformat(),
                "reviewed_at": d.reviewed_at.isoformat() if d.reviewed_at else None,
                "admin_notes": d.admin_notes
            } for d in documents]
        }), 200
        
    finally:
        db.close()

@admin_blueprint.get("/documents/<int:doc_id>/download")
@token_required
@role_required(UserRole.ADMIN)
def download_document(current_user, doc_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            return jsonify({"error": "Document not found"}), 404
        
        if not os.path.exists(document.file_path):
            return jsonify({"error": "File not found on disk"}), 404
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.file_name,
            mimetype=document.mime_type
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@admin_blueprint.get("/documents/<int:doc_id>/preview")
@token_required
@role_required(UserRole.ADMIN)
def preview_document(current_user, doc_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            return jsonify({"error": "Document not found"}), 404
        
        if not os.path.exists(document.file_path):
            return jsonify({"error": "File not found on disk"}), 404
        
        return send_file(
            document.file_path,
            mimetype=document.mime_type
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@admin_blueprint.delete("/users/<int:user_id>")
@token_required
@role_required(UserRole.ADMIN)
def delete_user(current_user, user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if user.role == UserRole.ADMIN:
            return jsonify({"error": "Cannot delete admin users"}), 403
        
        user.is_active = False
        db.commit()
        
        return jsonify({"message": f"User {user.email} soft deleted successfully"}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@admin_blueprint.get("/users/<int:user_id>")
@token_required
@role_required(UserRole.ADMIN)
def get_user_details(current_user, user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        
        if user.role == UserRole.PROFESSIONAL:
            professional = db.query(Professional).filter(Professional.user_id == user.id).first()
            if professional:
                user_data["professional"] = {
                    "id": professional.id,
                    "full_name": professional.full_name,
                    "phone_number": professional.phone_number,
                    "skills": professional.skills,
                    "hourly_rate": professional.hourly_rate,
                    "location": professional.location
                }
        elif user.role == UserRole.INSTITUTION:
            institution = db.query(Institution).filter(Institution.user_id == user.id).first()
            if institution:
                user_data["institution"] = {
                    "id": institution.id,
                    "institution_name": institution.institution_name,
                    "contact_email": institution.contact_email,
                    "contact_phone": institution.contact_phone,
                    "location": institution.location
                }
        
        return jsonify(user_data), 200
        
    finally:
        db.close()

@admin_blueprint.get("/payments/filter")
@token_required
@role_required(UserRole.ADMIN)
def filter_payments(current_user):
    db = SessionLocal()
    try:
        status = request.args.get('status')
        institution_id = request.args.get('institution_id')
        professional_id = request.args.get('professional_id')
        
        query = db.query(Payment)
        
        if status:
            try:
                status_enum = TransactionStatus[status.upper()]
                query = query.filter(Payment.status == status_enum)
            except KeyError:
                return jsonify({"error": "Invalid status"}), 400
        
        if institution_id:
            query = query.filter(Payment.institution_id == int(institution_id))
        
        if professional_id:
            query = query.filter(Payment.professional_id == int(professional_id))
        
        payments = query.all()
        
        return jsonify({
            "payments": [{
                "id": p.id,
                "gig_id": p.gig_id,
                "institution_id": p.institution_id,
                "professional_id": p.professional_id,
                "amount": p.amount,
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None
            } for p in payments]
        }), 200
        
    finally:
        db.close()
