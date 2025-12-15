from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.institution import Institution
from app.models.user import UserRole
from app.middleware.auth import token_required, role_required

institution_blueprint = Blueprint("institution", __name__)

@institution_blueprint.post("/profile")
@token_required
@role_required(UserRole.INSTITUTION)
def create_profile(current_user):
    db = SessionLocal()
    try:
        existing_profile = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if existing_profile:
            return jsonify({"error": "Profile already exists"}), 400
        
        data = request.json
        if not data or not data.get("institution_name"):
            return jsonify({"error": "Institution name is required"}), 400
        
        profile = Institution(
            user_id=current_user.id,
            institution_name=data["institution_name"],
            contact_email=data.get("contact_email"),
            contact_phone=data.get("contact_phone"),
            location=data.get("location"),
            description=data.get("description")
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        return jsonify({
            "message": "Profile created successfully",
            "profile": {
                "id": profile.id,
                "institution_name": profile.institution_name,
                "contact_email": profile.contact_email,
                "contact_phone": profile.contact_phone,
                "location": profile.location,
                "description": profile.description
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@institution_blueprint.get("/profile")
@token_required
@role_required(UserRole.INSTITUTION)
def get_profile(current_user):
    db = SessionLocal()
    try:
        profile = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        
        return jsonify({
            "id": profile.id,
            "institution_name": profile.institution_name,
            "contact_person": profile.contact_person,
            "phone": profile.phone,
            "email": profile.email,
            "address": profile.address,
            "description": profile.description,
            "website": profile.website
        }), 200
    finally:
        db.close()

@institution_blueprint.put("/profile")
@token_required
@role_required(UserRole.INSTITUTION)
def update_profile(current_user):
    db = SessionLocal()
    try:
        profile = db.query(Institution).filter(Institution.user_id == current_user.id).first()
        if not profile:
            return jsonify({"error": "Profile not found. Create one first."}), 404
        
        data = request.json
        if data.get("institution_name"):
            profile.institution_name = data["institution_name"]
        if "contact_person" in data:
            profile.contact_person = data["contact_person"]
        if "phone" in data:
            profile.phone = data["phone"]
        if "email" in data:
            profile.email = data["email"]
        if "address" in data:
            profile.address = data["address"]
        if "description" in data:
            profile.description = data["description"]
        if "website" in data:
            profile.website = data["website"]
        
        db.commit()
        db.refresh(profile)
        
        return jsonify({
            "message": "Profile updated successfully",
            "profile": {
                "id": profile.id,
                "institution_name": profile.institution_name,
                "contact_person": profile.contact_person,
                "phone": profile.phone,
                "email": profile.email,
                "address": profile.address,
                "description": profile.description,
                "website": profile.website
            }
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
