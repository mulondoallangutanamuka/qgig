from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.professional import Professional
from app.models.user import UserRole
from app.middleware.auth import token_required, role_required

professional_blueprint = Blueprint("professional", __name__)

@professional_blueprint.post("/profile")
@token_required
@role_required(UserRole.PROFESSIONAL)
def create_profile(current_user):
    db = SessionLocal()
    try:
        existing_profile = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        if existing_profile:
            return jsonify({"error": "Profile already exists"}), 400
        
        data = request.json
        if not data or not data.get("full_name"):
            return jsonify({"error": "Full name is required"}), 400
        
        profile = Professional(
            user_id=current_user.id,
            full_name=data["full_name"],
            phone_number=data.get("phone_number"),
            bio=data.get("bio"),
            skills=data.get("skills"),
            hourly_rate=data.get("hourly_rate"),
            daily_rate=data.get("daily_rate"),
            location=data.get("location")
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        return jsonify({
            "message": "Profile created successfully",
            "profile": {
                "id": profile.id,
                "full_name": profile.full_name,
                "phone_number": profile.phone_number,
                "bio": profile.bio,
                "skills": profile.skills,
                "hourly_rate": profile.hourly_rate,
                "daily_rate": profile.daily_rate,
                "location": profile.location
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@professional_blueprint.get("/profile")
@token_required
@role_required(UserRole.PROFESSIONAL)
def get_profile(current_user):
    db = SessionLocal()
    try:
        profile = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        
        return jsonify({
            "id": profile.id,
            "full_name": profile.full_name,
            "phone": profile.phone,
            "bio": profile.bio,
            "skills": profile.skills,
            "hourly_rate": profile.hourly_rate,
            "daily_rate": profile.daily_rate,
            "location": profile.location
        }), 200
    finally:
        db.close()

@professional_blueprint.put("/profile")
@token_required
@role_required(UserRole.PROFESSIONAL)
def update_profile(current_user):
    db = SessionLocal()
    try:
        profile = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        if not profile:
            return jsonify({"error": "Profile not found. Create one first."}), 404
        
        data = request.json
        if data.get("full_name"):
            profile.full_name = data["full_name"]
        if "phone" in data:
            profile.phone = data["phone"]
        if "bio" in data:
            profile.bio = data["bio"]
        if "skills" in data:
            profile.skills = data["skills"]
        if "hourly_rate" in data:
            profile.hourly_rate = data["hourly_rate"]
        if "daily_rate" in data:
            profile.daily_rate = data["daily_rate"]
        if "location" in data:
            profile.location = data["location"]
        
        db.commit()
        db.refresh(profile)
        
        return jsonify({
            "message": "Profile updated successfully",
            "profile": {
                "id": profile.id,
                "full_name": profile.full_name,
                "phone": profile.phone,
                "bio": profile.bio,
                "skills": profile.skills,
                "hourly_rate": profile.hourly_rate,
                "daily_rate": profile.daily_rate,
                "location": profile.location
            }
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
