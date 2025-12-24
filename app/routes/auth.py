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
        
        existing_user = db.query(User).filter(User.email == data["email"]).first()
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400
        
        hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
        
        # Create user with default professional role (for backward compatibility)
        user = User(
            email=data["email"],
            password=hashed.decode(),
            role=UserRole.PROFESSIONAL
        )
        db.add(user)
        db.flush()
        
        # Create BOTH profiles (multi-role support)
        from app.models.professional import Professional
        from app.models.institution import Institution
        
        professional_profile = Professional(user_id=user.id)
        institution_profile = Institution(user_id=user.id)
        db.add(professional_profile)
        db.add(institution_profile)
        db.flush()

        # Bootstrap into new roles tables
        from app.models.role import Role, UserRoleAssignment
        
        # Ensure professional and institution roles exist and assign both
        for role_name in ['professional', 'institution']:
            role_row = db.query(Role).filter(Role.name == role_name).first()
            if not role_row:
                role_row = Role(name=role_name, is_switchable=True)
                db.add(role_row)
                db.flush()
            
            # Assign role to user
            assignment = UserRoleAssignment(user_id=user.id, role_id=role_row.id)
            db.add(assignment)
        
        db.commit()
        db.refresh(user)
        
        return jsonify({
            "message": "User registered successfully. You can switch between Professional and Institution roles.",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role.value,
                "active_role": user.role.value,
                "available_roles": ["professional", "institution"]
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

        # Ensure role exists and assignment exists (migration-friendly)
        try:
            from app.models.role import Role, UserRoleAssignment

            role_row = db.query(Role).filter(Role.name == user.role.value).first()
            if not role_row:
                role_row = Role(name=user.role.value, is_switchable=(user.role != UserRole.ADMIN))
                db.add(role_row)
                db.commit()
                db.refresh(role_row)

            existing_assignment = db.query(UserRoleAssignment).filter(
                UserRoleAssignment.user_id == user.id,
                UserRoleAssignment.role_id == role_row.id
            ).first()
            if not existing_assignment:
                db.add(UserRoleAssignment(user_id=user.id, role_id=role_row.id))
                db.commit()
        except Exception:
            db.rollback()
        
        # Set active role (session preferred). Admin remains non-switchable.
        active_role = user.role.value

        # Create JWT token
        token = jwt.encode({
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value,
            'active_role': active_role,
            'exp': datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        }, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        # Also log in with Flask-Login for session persistence
        login_user(user, remember=True)
        session['user_id'] = user.id
        session['role'] = user.role.value
        session['active_role'] = active_role
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role.value,
                "active_role": active_role
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@auth_blueprint.get("/me")
@token_required
def get_current_user(current_user):
    active_role = session.get('active_role') or session.get('role') or session.get('user_role') or current_user.role.value

    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value,
        "active_role": active_role
    }), 200


@auth_blueprint.post("/switch-role")
@token_required
def switch_role(current_user):
    db = SessionLocal()
    try:
        data = request.json or {}
        requested_role = data.get('role')
        if not requested_role:
            return jsonify({"error": "Role is required"}), 400

        requested_role = str(requested_role).lower()
        if requested_role == UserRole.ADMIN.value:
            return jsonify({"error": "Cannot switch to admin role"}), 400

        from app.models.role import Role, UserRoleAssignment, RoleSwitchAudit

        role_row = db.query(Role).filter(Role.name == requested_role).first()
        if not role_row:
            return jsonify({"error": "Unknown role"}), 400

        if not role_row.is_switchable:
            return jsonify({"error": "Role is not switchable"}), 400

        assignment = db.query(UserRoleAssignment).filter(
            UserRoleAssignment.user_id == current_user.id,
            UserRoleAssignment.role_id == role_row.id
        ).first()

        # Auto-create missing role assignments for existing users
        if not assignment:
            # Create both professional and institution role assignments if they don't exist
            for role_name in ['professional', 'institution']:
                role_to_assign = db.query(Role).filter(Role.name == role_name).first()
                if not role_to_assign:
                    role_to_assign = Role(name=role_name, is_switchable=True)
                    db.add(role_to_assign)
                    db.flush()
                
                existing = db.query(UserRoleAssignment).filter(
                    UserRoleAssignment.user_id == current_user.id,
                    UserRoleAssignment.role_id == role_to_assign.id
                ).first()
                
                if not existing:
                    new_assignment = UserRoleAssignment(
                        user_id=current_user.id,
                        role_id=role_to_assign.id
                    )
                    db.add(new_assignment)
            
            # Create missing profiles if needed
            from app.models.professional import Professional
            from app.models.institution import Institution
            
            prof = db.query(Professional).filter(Professional.user_id == current_user.id).first()
            if not prof:
                db.add(Professional(user_id=current_user.id))
            
            inst = db.query(Institution).filter(Institution.user_id == current_user.id).first()
            if not inst:
                db.add(Institution(user_id=current_user.id))
            
            db.flush()

        from_role = session.get('active_role') or session.get('role') or session.get('user_role')
        session['active_role'] = requested_role

        audit = RoleSwitchAudit(
            user_id=current_user.id,
            from_role=from_role,
            to_role=requested_role,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.add(audit)
        db.commit()

        # Best-effort: issue a new JWT with updated active_role
        token = jwt.encode({
            'user_id': current_user.id,
            'email': current_user.email,
            'role': current_user.role.value,
            'active_role': requested_role,
            'exp': datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        }, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        return jsonify({
            "message": "Role switched successfully",
            "token": token,
            "active_role": requested_role
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

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
