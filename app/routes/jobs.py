from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.job import Job, GigInterest, JobStatus
from app.models.institution import Institution
from app.models.professional import Professional
from app.models.user import UserRole
from app.middleware.auth import token_required, role_required
from datetime import datetime

jobs_blueprint = Blueprint("jobs", __name__)

@jobs_blueprint.post("")
@token_required
@role_required(UserRole.INSTITUTION)
def create_job(current_user):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not institution:
            return jsonify({"error": "Institution profile not found. Create one first."}), 404
        
        data = request.json
        if not data or not data.get('title') or not data.get('description'):
            return jsonify({"error": "Title and description are required"}), 400
        
        if not data.get('location') or not data.get('pay_amount'):
            return jsonify({"error": "Location and pay amount are required"}), 400
        
        job = Job(
            institution_id=institution.id,
            title=data['title'],
            description=data['description'],
            location=data['location'],
            pay_amount=float(data['pay_amount']),
            duration_hours=data.get('duration_hours'),
            is_urgent=data.get('is_urgent', False),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        return jsonify({
            "message": "Job created successfully",
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "location": job.location,
            "pay_amount": job.pay_amount,
            "status": job.status.value,
            "created_at": job.created_at.isoformat()
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@jobs_blueprint.get("")
def list_jobs():
    db = SessionLocal()
    try:
        status_filter = request.args.get('status', 'open')
        
        query = db.query(Job).filter(Job.status == JobStatus.OPEN)
        jobs = query.order_by(Job.created_at.desc()).all()
        
        return jsonify({
            "jobs": [{
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "requirements": job.requirements,
                "job_type": job.job_type.value,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "deadline": job.deadline.isoformat() if job.deadline else None,
                "institution": {
                    "id": job.institution.id,
                    "name": job.institution.institution_name
                }
            } for job in jobs]
        }), 200
    finally:
        db.close()

@jobs_blueprint.get("/<int:job_id>")
def get_job(job_id):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        return jsonify({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "job_type": job.job_type.value,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "deadline": job.deadline.isoformat() if job.deadline else None,
            "institution": {
                "id": job.institution.id,
                "name": job.institution.institution_name,
                "description": job.institution.description
            }
        }), 200
    finally:
        db.close()

@jobs_blueprint.get("/my-gigs")
@token_required
@role_required(UserRole.INSTITUTION)
def get_my_gigs(current_user):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not institution:
            return jsonify({"error": "Institution profile not found"}), 404
        
        jobs = db.query(Job).filter(Job.institution_id == institution.id).order_by(Job.created_at.desc()).all()
        
        return jsonify({
            "gigs": [{
                "id": job.id,
                "title": job.title,
                "location": job.location,
                "pay_amount": job.pay_amount,
                "is_urgent": job.is_urgent,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "interest_count": len(job.interests),
                "assigned_to": job.assigned_professional.full_name if job.assigned_professional else None
            } for job in jobs]
        }), 200
    finally:
        db.close()

@jobs_blueprint.put("/<int:job_id>")
@token_required
@role_required(UserRole.INSTITUTION)
def update_job(current_user, job_id):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not institution:
            return jsonify({"error": "Institution profile not found"}), 404
        
        job = db.query(Job).filter(Job.id == job_id, Job.institution_id == institution.id).first()
        if not job:
            return jsonify({"error": "Job not found or unauthorized"}), 404
        
        data = request.json
        if data.get('title'):
            job.title = data['title']
        if data.get('description'):
            job.description = data['description']
        if 'requirements' in data:
            job.requirements = data['requirements']
        if data.get('job_type'):
            job.job_type = JobType[data['job_type'].upper()]
        if 'location' in data:
            job.location = data['location']
        if 'salary_min' in data:
            job.salary_min = data['salary_min']
        if 'salary_max' in data:
            job.salary_max = data['salary_max']
        if data.get('status'):
            job.status = JobStatus[data['status'].upper()]
        
        job.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({"message": "Job updated successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@jobs_blueprint.delete("/<int:job_id>")
@token_required
@role_required(UserRole.INSTITUTION)
def delete_gig(current_user, job_id):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not institution:
            return jsonify({"error": "Institution profile not found"}), 404

        job = db.query(Job).filter(Job.id == job_id, Job.institution_id == institution.id).first()
        if not job:
            return jsonify({"error": "Gig not found or unauthorized"}), 404

        # Get interested professionals before deleting
        interested_professionals_user_ids = [interest.professional.user_id for interest in job.interests]

        # Invalidate related interests before deleting
        db.query(GigInterest).filter(GigInterest.job_id == job_id).delete()

        db.delete(job)
        db.commit()

        from app import socketio
        for user_id in interested_professionals_user_ids:
            socketio.emit('notification', {
                'message': f'The gig "{job.title}" is no longer available.'
            }, room=f'user_{user_id}')

        return jsonify({"message": "Gig deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@jobs_blueprint.post("/<int:job_id>/express-interest")
@token_required
@role_required(UserRole.PROFESSIONAL)
def express_interest(current_user, job_id):
    from app.models.notification import Notification
    from app.models.user import User
    import logging
    
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    
    try:
        professional = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        if not professional:
            return jsonify({"error": "Professional profile not found. Create one first."}), 404
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return jsonify({"error": "Gig not found"}), 404
        
        if job.status != JobStatus.OPEN:
            return jsonify({"error": "Gig is no longer available"}), 400
        
        existing_interest = db.query(GigInterest).filter(
            GigInterest.job_id == job_id,
            GigInterest.professional_id == professional.id
        ).first()
        
        if existing_interest:
            return jsonify({"error": "You have already expressed interest in this gig"}), 400
        
        # Create interest
        interest = GigInterest(
            job_id=job_id,
            professional_id=professional.id
        )
        db.add(interest)
        
        # Create notification for institution
        notification = Notification(
            user_id=job.institution.user_id,
            title="New Interest in Your Job",
            message=f"{professional.full_name} has expressed interest in your job: {job.title}",
            job_interest_id=interest.id
        )
        db.add(notification)
        
        # COMMIT BEFORE EMITTING
        db.commit()
        db.refresh(interest)
        db.refresh(notification)
        
        logger.info(f"Interest {interest.id} created, notification {notification.id} saved")
        
        # Send real-time notification via Socket.IO AFTER commit
        try:
            from app.sockets import send_interest_notification
            institution_id = job.institution.id
            notification_data = {
                'notification_id': notification.id,
                'professional_id': professional.id,
                'professional_name': professional.full_name,
                'job_id': job.id,
                'job_title': job.title,
                'institution_id': institution_id,
                'message': notification.message,
                'timestamp': notification.created_at.isoformat()
            }
            send_interest_notification(institution_id, notification_data)
            logger.info("Socket.IO notification sent successfully")
        except Exception as socket_error:
            logger.error(f"Socket.IO emission failed: {socket_error}", exc_info=True)
        
        # ALWAYS return success response
        return jsonify({
            "success": True,
            "message": "Interest registered! Institution will review and may assign you.",
            "interest_id": interest.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error in express_interest: {e}", exc_info=True)
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@jobs_blueprint.post("/<int:job_id>/assign/<int:professional_id>")
@token_required
@role_required(UserRole.INSTITUTION)
def assign_gig(current_user, job_id, professional_id):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not institution:
            return jsonify({"error": "Institution profile not found"}), 404
        
        job = db.query(Job).filter(Job.id == job_id, Job.institution_id == institution.id).first()
        if not job:
            return jsonify({"error": "Gig not found or unauthorized"}), 404
        
        if job.status != JobStatus.OPEN:
            return jsonify({"error": "Gig is not open"}), 400
        
        professional = db.query(Professional).filter(Professional.id == professional_id).first()
        if not professional:
            return jsonify({"error": "Professional not found"}), 404
        
        job.assigned_professional_id = professional_id
        job.status = JobStatus.ASSIGNED
        job.updated_at = datetime.utcnow()
        
        db.commit()
        
        return jsonify({
            "message": "Gig assigned successfully",
            "assigned_to": professional.full_name
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@jobs_blueprint.get("/my-gigs-professional")
@token_required
@role_required(UserRole.PROFESSIONAL)
def get_my_assigned_gigs(current_user):
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        if not professional:
            return jsonify({"error": "Professional profile not found"}), 404
        
        assigned_gigs = db.query(Job).filter(Job.assigned_professional_id == professional.id).all()
        interests = db.query(GigInterest).filter(GigInterest.professional_id == professional.id).all()
        
        return jsonify({
            "assigned_gigs": [{
                "id": gig.id,
                "title": gig.title,
                "location": gig.location,
                "pay_amount": gig.pay_amount,
                "status": gig.status.value,
                "institution": gig.institution.institution_name,
                "start_date": gig.start_date.isoformat() if gig.start_date else None
            } for gig in assigned_gigs],
            "interested_gigs": [{
                "id": interest.job.id,
                "title": interest.job.title,
                "location": interest.job.location,
                "pay_amount": interest.job.pay_amount,
                "expressed_at": interest.created_at.isoformat()
            } for interest in interests if interest.job.status == JobStatus.OPEN]
        }), 200
    finally:
        db.close()

@jobs_blueprint.get("/<int:job_id>/interested-professionals")
@token_required
@role_required(UserRole.INSTITUTION)
def get_interested_professionals(current_user, job_id):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not institution:
            return jsonify({"error": "Institution profile not found"}), 404
        
        job = db.query(Job).filter(Job.id == job_id, Job.institution_id == institution.id).first()
        if not job:
            return jsonify({"error": "Gig not found or unauthorized"}), 404
        
        interests = db.query(GigInterest).filter(GigInterest.job_id == job_id).all()
        
        return jsonify({
            "interested_professionals": [{
                "id": interest.professional.id,
                "name": interest.professional.full_name,
                "skills": interest.professional.skills,
                "hourly_rate": interest.professional.hourly_rate,
                "location": interest.professional.location,
                "expressed_at": interest.created_at.isoformat()
            } for interest in interests]
        }), 200
    finally:
        db.close()

@jobs_blueprint.get("/<int:job_id>/check-interest")
@token_required
@role_required(UserRole.PROFESSIONAL)
def check_interest_status(current_user, job_id):
    """Check if current user has already expressed interest in this job"""
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        if not professional:
            return jsonify({"has_interest": False}), 200
        
        existing_interest = db.query(GigInterest).filter(
            GigInterest.job_id == job_id,
            GigInterest.professional_id == professional.id
        ).first()
        
        return jsonify({
            "has_interest": existing_interest is not None,
            "interest_id": existing_interest.id if existing_interest else None,
            "expressed_at": existing_interest.created_at.isoformat() if existing_interest else None
        }), 200
    finally:
        db.close()

@jobs_blueprint.post("/<int:job_id>/cancel-interest")
@token_required
@role_required(UserRole.PROFESSIONAL)
def cancel_interest(current_user, job_id):
    from app.models.notification import Notification
    from app import socketio

    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        if not professional:
            return jsonify({"error": "Professional profile not found"}), 404

        interest = db.query(GigInterest).filter(
            GigInterest.job_id == job_id,
            GigInterest.professional_id == professional.id
        ).first()

        if not interest:
            return jsonify({"error": "Interest not found"}), 404

        job = interest.job
        institution_user_id = job.institution.user_id

        db.delete(interest)
        db.commit()

        # Real-time notification to the institution
        notification_message = "The professional has withdrawn their interest in this gig."
        socketio.emit('notification', {
            'message': notification_message
        }, room=f'user_{institution_user_id}')

        return jsonify({"message": "Interest canceled successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@jobs_blueprint.post("/<int:job_id>/close")
@token_required
@role_required(UserRole.INSTITUTION)
def close_gig(current_user, job_id):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not institution:
            return jsonify({"error": "Institution profile not found"}), 404

        job = db.query(Job).filter(Job.id == job_id, Job.institution_id == institution.id).first()
        if not job:
            return jsonify({"error": "Gig not found or unauthorized"}), 404

        if job.status == JobStatus.CLOSED:
            return jsonify({"error": "Gig is already closed"}), 400

        job.status = JobStatus.CLOSED
        job.updated_at = datetime.utcnow()
        db.commit()

        from app import socketio
        socketio.emit('gig_update', {'gig_id': job_id, 'status': 'closed'}, room=f'institution_{institution.id}')

        return jsonify({"message": "Gig closed successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
