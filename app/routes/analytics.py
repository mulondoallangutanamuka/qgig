from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.job import Job, JobStatus
from app.models.payment import Payment, TransactionStatus
from app.models.document import Document, DocumentStatus
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.rating import Rating
from app.middleware.auth import token_required, role_required
from sqlalchemy import func, extract, and_
from datetime import datetime, timedelta

analytics_blueprint = Blueprint("analytics", __name__)

@analytics_blueprint.get("/admin/dashboard")
@token_required
@role_required(UserRole.ADMIN)
def admin_analytics(current_user):
    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        total_professionals = db.query(Professional).count()
        total_institutions = db.query(Institution).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        
        total_gigs = db.query(Job).count()
        open_gigs = db.query(Job).filter(Job.status == JobStatus.OPEN).count()
        assigned_gigs = db.query(Job).filter(Job.status == JobStatus.ASSIGNED).count()
        completed_gigs = db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        
        total_payments = db.query(Payment).count()
        completed_payments = db.query(Payment).filter(Payment.status == TransactionStatus.COMPLETED).count()
        pending_payments = db.query(Payment).filter(Payment.status == TransactionStatus.PENDING).count()
        failed_payments = db.query(Payment).filter(Payment.status == TransactionStatus.FAILED).count()
        
        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        pending_documents = db.query(Document).filter(Document.status == DocumentStatus.PENDING).count()
        approved_documents = db.query(Document).filter(Document.status == DocumentStatus.APPROVED).count()
        rejected_documents = db.query(Document).filter(Document.status == DocumentStatus.REJECTED).count()
        
        avg_rating = db.query(func.avg(Rating.rating)).scalar() or 0
        total_ratings = db.query(Rating).count()
        
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        revenue_last_30_days = db.query(func.sum(Payment.amount)).filter(
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= thirty_days_ago
        ).scalar() or 0
        
        revenue_last_7_days = db.query(func.sum(Payment.amount)).filter(
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= seven_days_ago
        ).scalar() or 0
        
        gigs_last_30_days = db.query(Job).filter(Job.created_at >= thirty_days_ago).count()
        
        most_active_institutions = db.query(
            Institution.id,
            Institution.institution_name,
            func.count(Job.id).label('gig_count')
        ).join(Job).group_by(Institution.id, Institution.institution_name).order_by(
            func.count(Job.id).desc()
        ).limit(5).all()
        
        most_hired_professionals = db.query(
            Professional.id,
            Professional.full_name,
            func.count(Job.id).label('hire_count')
        ).join(Job, Job.assigned_professional_id == Professional.id).filter(
            Job.status.in_([JobStatus.ASSIGNED, JobStatus.COMPLETED])
        ).group_by(Professional.id, Professional.full_name).order_by(
            func.count(Job.id).desc()
        ).limit(5).all()
        
        daily_revenue = db.query(
            func.date(Payment.completed_at).label('date'),
            func.sum(Payment.amount).label('revenue')
        ).filter(
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= thirty_days_ago
        ).group_by(func.date(Payment.completed_at)).order_by(func.date(Payment.completed_at)).all()
        
        return jsonify({
            "users": {
                "total": total_users,
                "professionals": total_professionals,
                "institutions": total_institutions,
                "active": active_users
            },
            "gigs": {
                "total": total_gigs,
                "open": open_gigs,
                "assigned": assigned_gigs,
                "completed": completed_gigs,
                "last_30_days": gigs_last_30_days
            },
            "payments": {
                "total": total_payments,
                "completed": completed_payments,
                "pending": pending_payments,
                "failed": failed_payments,
                "total_revenue": float(total_revenue),
                "revenue_last_30_days": float(revenue_last_30_days),
                "revenue_last_7_days": float(revenue_last_7_days)
            },
            "documents": {
                "pending": pending_documents,
                "approved": approved_documents,
                "rejected": rejected_documents
            },
            "ratings": {
                "average": round(float(avg_rating), 2),
                "total": total_ratings
            },
            "top_institutions": [{
                "id": inst.id,
                "name": inst.institution_name,
                "gig_count": inst.gig_count
            } for inst in most_active_institutions],
            "top_professionals": [{
                "id": prof.id,
                "name": prof.full_name,
                "hire_count": prof.hire_count
            } for prof in most_hired_professionals],
            "daily_revenue": [{
                "date": str(dr.date),
                "revenue": float(dr.revenue)
            } for dr in daily_revenue]
        }), 200
        
    finally:
        db.close()

@analytics_blueprint.get("/institution/dashboard")
@token_required
@role_required(UserRole.INSTITUTION)
def institution_analytics(current_user):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not institution:
            return jsonify({"error": "Institution profile not found"}), 404
        
        total_gigs = db.query(Job).filter(Job.institution_id == institution.id).count()
        open_gigs = db.query(Job).filter(
            Job.institution_id == institution.id,
            Job.status == JobStatus.OPEN
        ).count()
        assigned_gigs = db.query(Job).filter(
            Job.institution_id == institution.id,
            Job.status == JobStatus.ASSIGNED
        ).count()
        completed_gigs = db.query(Job).filter(
            Job.institution_id == institution.id,
            Job.status == JobStatus.COMPLETED
        ).count()
        
        total_payments = db.query(func.sum(Payment.amount)).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        pending_payments_count = db.query(Payment).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.PENDING
        ).count()
        
        completed_payments_count = db.query(Payment).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.COMPLETED
        ).count()
        
        top_professionals = db.query(
            Professional.id,
            Professional.full_name,
            func.count(Job.id).label('hire_count')
        ).join(Job, Job.assigned_professional_id == Professional.id).filter(
            Job.institution_id == institution.id,
            Job.status.in_([JobStatus.ASSIGNED, JobStatus.COMPLETED])
        ).group_by(Professional.id, Professional.full_name).order_by(
            func.count(Job.id).desc()
        ).limit(5).all()
        
        avg_rating_given = db.query(func.avg(Rating.rating)).filter(
            Rating.institution_id == institution.id
        ).scalar() or 0
        
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        monthly_spending = db.query(func.sum(Payment.amount)).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= thirty_days_ago
        ).scalar() or 0
        
        return jsonify({
            "gigs": {
                "total": total_gigs,
                "open": open_gigs,
                "assigned": assigned_gigs,
                "completed": completed_gigs
            },
            "payments": {
                "total_spent": float(total_payments),
                "pending_count": pending_payments_count,
                "completed_count": completed_payments_count,
                "monthly_spending": float(monthly_spending)
            },
            "top_professionals": [{
                "id": prof.id,
                "name": prof.full_name,
                "hire_count": prof.hire_count
            } for prof in top_professionals],
            "ratings": {
                "average_given": round(float(avg_rating_given), 2)
            }
        }), 200
        
    finally:
        db.close()

@analytics_blueprint.get("/professional/dashboard")
@token_required
@role_required(UserRole.PROFESSIONAL)
def professional_analytics(current_user):
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        if not professional:
            return jsonify({"error": "Professional profile not found"}), 404
        
        total_gigs = db.query(Job).filter(
            Job.assigned_professional_id == professional.id
        ).count()
        
        completed_gigs = db.query(Job).filter(
            Job.assigned_professional_id == professional.id,
            Job.status == JobStatus.COMPLETED
        ).count()
        
        active_gigs = db.query(Job).filter(
            Job.assigned_professional_id == professional.id,
            Job.status == JobStatus.ASSIGNED
        ).count()
        
        total_earnings = db.query(func.sum(Payment.amount)).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        pending_payments = db.query(func.sum(Payment.amount)).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.PENDING
        ).scalar() or 0
        
        avg_rating = db.query(func.avg(Rating.rating)).filter(
            Rating.professional_id == professional.id
        ).scalar() or 0
        
        total_ratings = db.query(Rating).filter(
            Rating.professional_id == professional.id
        ).count()
        
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        monthly_earnings = db.query(func.sum(Payment.amount)).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= thirty_days_ago
        ).scalar() or 0
        
        monthly_earnings_trend = db.query(
            extract('month', Payment.completed_at).label('month'),
            extract('year', Payment.completed_at).label('year'),
            func.sum(Payment.amount).label('earnings')
        ).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= datetime.utcnow() - timedelta(days=180)
        ).group_by(
            extract('year', Payment.completed_at),
            extract('month', Payment.completed_at)
        ).order_by(
            extract('year', Payment.completed_at),
            extract('month', Payment.completed_at)
        ).all()
        
        document_status = db.query(
            Document.status,
            func.count(Document.id).label('count')
        ).filter(
            Document.professional_id == professional.id
        ).group_by(Document.status).all()
        
        return jsonify({
            "gigs": {
                "total": total_gigs,
                "completed": completed_gigs,
                "active": active_gigs
            },
            "earnings": {
                "total": float(total_earnings),
                "pending": float(pending_payments),
                "monthly": float(monthly_earnings)
            },
            "ratings": {
                "average": round(float(avg_rating), 2),
                "total": total_ratings
            },
            "monthly_trend": [{
                "month": int(trend.month),
                "year": int(trend.year),
                "earnings": float(trend.earnings)
            } for trend in monthly_earnings_trend],
            "documents": {
                status.status.value: status.count for status in document_status
            }
        }), 200
        
    finally:
        db.close()
