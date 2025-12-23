from functools import wraps
from flask import request, jsonify, session
import jwt
from app.config import settings
from app.database import SessionLocal
from app.models.user import User, UserRole


def _normalize_role_value(role_value):
    if role_value is None:
        return None
    if isinstance(role_value, str):
        return role_value
    return getattr(role_value, "value", str(role_value))


def _get_active_role_from_request():
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        try:
            token = auth_header.split(" ")[1]
            data = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            active_role = data.get('active_role') or data.get('role')
            if active_role:
                return str(active_role)
        except Exception:
            pass

    active_role = session.get('active_role') or session.get('role') or session.get('user_role')
    if active_role:
        return str(active_role)
    return None


def _user_has_role(db, user, role_name: str) -> bool:
    if not user or not role_name:
        return False

    # Prefer new many-to-many relationship
    try:
        from app.models.role import Role, UserRoleAssignment
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            exists = db.query(UserRoleAssignment).filter(
                UserRoleAssignment.user_id == user.id,
                UserRoleAssignment.role_id == role.id
            ).first()
            if exists:
                return True
    except Exception:
        pass

    # Backward-compatible fallback
    return _normalize_role_value(getattr(user, "role", None)) == role_name

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = None
        
        # Try JWT authentication first
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
                data = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                db = SessionLocal()
                current_user = db.query(User).filter(User.id == data['user_id']).first()
                db.close()
                
                if not current_user:
                    return jsonify({"error": "Invalid token"}), 401
                    
            except IndexError:
                return jsonify({"error": "Invalid token format"}), 401
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
        
        # Fallback to session-based authentication
        elif 'user_id' in session:
            db = SessionLocal()
            current_user = db.query(User).filter(User.id == session['user_id']).first()
            db.close()
            
            if not current_user:
                return jsonify({"error": "Invalid session"}), 401
        
        # No authentication found
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            active_role = _get_active_role_from_request()
            if not active_role:
                return jsonify({"error": "Access forbidden: missing active role"}), 403

            allowed_role_names = set(_normalize_role_value(r) for r in allowed_roles)
            if active_role not in allowed_role_names:
                return jsonify({"error": "Access forbidden: insufficient permissions"}), 403

            db = SessionLocal()
            try:
                if not _user_has_role(db, current_user, active_role):
                    return jsonify({"error": "Access forbidden: role not assigned to user"}), 403
            finally:
                db.close()

            return f(current_user, *args, **kwargs)
        return decorated
    return decorator


def require_role(*allowed_roles):
    return role_required(*allowed_roles)
