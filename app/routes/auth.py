from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, current_user
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.config import settings
from app.middleware.auth import token_required, role_required
import bcrypt
import jwt
from datetime import datetime, timedelta

auth_blueprint = Blueprint("auth", __name__)

@auth_blueprint.post("/register")
def register():
    db = SessionLocal()
    try:
        data = request.json
        
        if not data or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email and password are required"}), 400
        
        if not data.get("role"):
            return jsonify({"error": "Role is required (professional or institution)"}), 400
        
        existing_user = db.query(User).filter(User.email == data["email"]).first()
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400
        
        try:
            role = UserRole[data["role"].upper()]
            if role == UserRole.ADMIN:
                return jsonify({"error": "Cannot register as admin"}), 400
        except KeyError:
            return jsonify({"error": "Invalid role. Must be 'professional' or 'institution'"}), 400
        
        hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
        
        user = User(
            email=data["email"],
            password=hashed.decode(),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role.value
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@auth_blueprint.post("/login")
def login():
    db = SessionLocal()
    try:
        data = request.json
        
        if not data or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email and password are required"}), 400
        
        user = db.query(User).filter(User.email == data["email"]).first()
        
        if not user or not bcrypt.checkpw(data["password"].encode(), user.password.encode()):
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Create JWT token
        token = jwt.encode({
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value,
            'exp': datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        }, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        # Also log in with Flask-Login for session persistence
        login_user(user, remember=True)
        session['user_id'] = user.id
        session['role'] = user.role.value
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role.value
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@auth_blueprint.get("/me")
@token_required
def get_current_user(current_user):
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value
    }), 200

@auth_blueprint.get("/admin-only")
@token_required
@role_required(UserRole.ADMIN)
def admin_only(current_user):
    return jsonify({"message": "Welcome admin!"}), 200

@auth_blueprint.get("/professional-only")
@token_required
@role_required(UserRole.PROFESSIONAL)
def professional_only(current_user):
    return jsonify({"message": "Welcome professional!"}), 200

@auth_blueprint.get("/institution-only")
@token_required
@role_required(UserRole.INSTITUTION)
def institution_only(current_user):
    return jsonify({"message": "Welcome institution!"}), 200

@auth_blueprint.post("/logout")
def logout():
    """Logout user and clear session"""
    logout_user()
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200
