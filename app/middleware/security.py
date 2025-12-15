from flask import request, jsonify
from functools import wraps
import re
import html
from datetime import datetime, timedelta

# Rate limiting storage (in-memory for simplicity, use Redis in production)
rate_limit_storage = {}

def sanitize_input(data):
    """Sanitize user input to prevent XSS and injection attacks"""
    if isinstance(data, str):
        # Remove HTML tags and escape special characters
        data = html.escape(data)
        # Remove potentially dangerous characters
        data = re.sub(r'[<>"\']', '', data)
        return data.strip()
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone.replace(' ', '').replace('-', '')) is not None

def rate_limit(max_requests=100, window_seconds=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.remote_addr
            current_time = datetime.utcnow()
            
            # Initialize or get rate limit data for this IP
            if client_ip not in rate_limit_storage:
                rate_limit_storage[client_ip] = []
            
            # Remove old requests outside the time window
            rate_limit_storage[client_ip] = [
                req_time for req_time in rate_limit_storage[client_ip]
                if current_time - req_time < timedelta(seconds=window_seconds)
            ]
            
            # Check if rate limit exceeded
            if len(rate_limit_storage[client_ip]) >= max_requests:
                return jsonify({
                    "error": "Rate limit exceeded. Please try again later."
                }), 429
            
            # Add current request
            rate_limit_storage[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_file_upload(file, allowed_extensions={'pdf', 'jpg', 'jpeg', 'png'}, max_size_mb=5):
    """Validate file upload"""
    if not file:
        return False, "No file provided"
    
    # Check file extension
    if '.' not in file.filename:
        return False, "File has no extension"
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size (read first to get size)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if size > max_size_bytes:
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    
    return True, "File valid"

def sanitize_filename(filename):
    """Sanitize filename to prevent directory traversal"""
    # Remove path separators and keep only the filename
    filename = filename.replace('\\', '').replace('/', '')
    # Remove potentially dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    return filename

def require_https(f):
    """Decorator to enforce HTTPS in production"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In production, uncomment this:
        # if not request.is_secure:
        #     return jsonify({"error": "HTTPS required"}), 403
        return f(*args, **kwargs)
    return decorated_function
