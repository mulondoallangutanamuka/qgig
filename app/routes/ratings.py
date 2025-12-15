from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.rating import Rating
from app.models.job import Job, JobStatus
from app.models.user import User
from app.models.professional import Professional
from app.models.institution import Institution
from app.middleware.auth import token_required
from sqlalchemy import func

ratings_blueprint = Blueprint("ratings", __name__)

@ratings_blueprint.post("/rate")
@token_required
def create_rating(current_user):
    db = SessionLocal()
    try:
        data = request.json
        gig_id = data.get('gig_id')
        rating_value = data.get('rating')
        review_text = data.get('review', '')
        
        if not gig_id or not rating_value:
            return jsonify({"error": "Gig ID and rating are required"}), 400
        
        if rating_value < 1 or rating_value > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
        
        gig = db.query(Job).filter(Job.id == gig_id).first()
        if not gig:
            return jsonify({"error": "Gig not found"}), 404
        
        if gig.status != JobStatus.COMPLETED:
            return jsonify({"error": "Can only rate completed gigs"}), 400
        
        professional = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        institution = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        
        if professional:
            if gig.assigned_professional_id != professional.id:
                return jsonify({"error": "You were not assigned to this gig"}), 403
            rated_user = db.query(User).join(Institution).filter(Institution.id == gig.institution_id).first()
        elif institution:
            if gig.institution_id != institution.id:
                return jsonify({"error": "This is not your gig"}), 403
            rated_user = db.query(User).join(Professional).filter(Professional.id == gig.assigned_professional_id).first()
        else:
            return jsonify({"error": "Profile not found"}), 404
        
        existing_rating = db.query(Rating).filter(
            Rating.gig_id == gig_id,
            Rating.rater_id == current_user.id
        ).first()
        
        if existing_rating:
            return jsonify({"error": "You have already rated this gig"}), 400
        
        new_rating = Rating(
            gig_id=gig_id,
            rater_id=current_user.id,
            rated_id=rated_user.id,
            rating=rating_value,
            review=review_text
        )
        
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        
        return jsonify({
            "message": "Rating submitted successfully",
            "rating_id": new_rating.id
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@ratings_blueprint.get("/user/<int:user_id>/ratings")
def get_user_ratings(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        ratings = db.query(Rating).filter(Rating.rated_id == user_id).all()
        
        avg_rating = db.query(func.avg(Rating.rating)).filter(Rating.rated_id == user_id).scalar()
        
        return jsonify({
            "user_id": user_id,
            "average_rating": round(float(avg_rating), 2) if avg_rating else 0,
            "total_ratings": len(ratings),
            "ratings": [{
                "id": r.id,
                "rating": r.rating,
                "review": r.review,
                "rater_name": r.rater.email,
                "created_at": r.created_at.isoformat()
            } for r in ratings]
        }), 200
        
    finally:
        db.close()

@ratings_blueprint.get("/gig/<int:gig_id>/ratings")
@token_required
def get_gig_ratings(current_user, gig_id):
    db = SessionLocal()
    try:
        gig = db.query(Job).filter(Job.id == gig_id).first()
        if not gig:
            return jsonify({"error": "Gig not found"}), 404
        
        ratings = db.query(Rating).filter(Rating.gig_id == gig_id).all()
        
        return jsonify({
            "gig_id": gig_id,
            "ratings": [{
                "id": r.id,
                "rating": r.rating,
                "review": r.review,
                "rater_email": r.rater.email,
                "rated_email": r.rated.email,
                "created_at": r.created_at.isoformat()
            } for r in ratings]
        }), 200
        
    finally:
        db.close()

@ratings_blueprint.get("/my-ratings")
@token_required
def get_my_ratings(current_user):
    db = SessionLocal()
    try:
        ratings_received = db.query(Rating).filter(Rating.rated_id == current_user.id).all()
        ratings_given = db.query(Rating).filter(Rating.rater_id == current_user.id).all()
        
        avg_rating = db.query(func.avg(Rating.rating)).filter(Rating.rated_id == current_user.id).scalar()
        
        return jsonify({
            "average_rating": round(float(avg_rating), 2) if avg_rating else 0,
            "total_received": len(ratings_received),
            "total_given": len(ratings_given),
            "ratings_received": [{
                "id": r.id,
                "rating": r.rating,
                "review": r.review,
                "rater_email": r.rater.email,
                "gig_title": r.gig.title,
                "created_at": r.created_at.isoformat()
            } for r in ratings_received],
            "ratings_given": [{
                "id": r.id,
                "rating": r.rating,
                "review": r.review,
                "rated_email": r.rated.email,
                "gig_title": r.gig.title,
                "created_at": r.created_at.isoformat()
            } for r in ratings_given]
        }), 200
        
    finally:
        db.close()
