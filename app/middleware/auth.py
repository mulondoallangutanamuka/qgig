from functools import wraps
from flask import request, jsonify
import jwt
from app.config import settings
from app.database import SessionLocal
from app.models.user import User, UserRole

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"error": "Invalid token format"}), 401
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        try:
            data = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            db = SessionLocal()
            current_user = db.query(User).filter(User.id == data['user_id']).first()
            db.close()
            
            if not current_user:
                return jsonify({"error": "Invalid token"}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({"error": "Access forbidden: insufficient permissions"}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator
