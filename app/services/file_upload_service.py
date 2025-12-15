"""
Secure File Upload Service
Handles file uploads with validation, security checks, and storage
"""
import os
import uuid
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from typing import Optional, Tuple, Dict
import mimetypes

class FileUploadService:
    """Service for handling secure file uploads"""
    
    # File size limits in bytes
    MAX_CV_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_CERTIFICATE_SIZE = 2 * 1024 * 1024  # 2MB
    MAX_PROFILE_PICTURE_SIZE = 1 * 1024 * 1024  # 1MB
    
    # Allowed MIME types
    ALLOWED_CV_TYPES = {
        'application/pdf': '.pdf',
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'
    }
    
    ALLOWED_CERTIFICATE_TYPES = {
        'application/pdf': '.pdf',
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png'
    }
    
    ALLOWED_PROFILE_PICTURE_TYPES = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png'
    }
    
    UPLOAD_BASE_DIR = os.path.join('app', 'static', 'uploads')
    
    @staticmethod
    def validate_file(file: FileStorage, file_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file based on type
        Returns: (is_valid, error_message)
        """
        if not file or not file.filename:
            return False, "No file provided"
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_type == 'cv':
            max_size = FileUploadService.MAX_CV_SIZE
            allowed_types = FileUploadService.ALLOWED_CV_TYPES
            type_name = "CV"
        elif file_type == 'certificate':
            max_size = FileUploadService.MAX_CERTIFICATE_SIZE
            allowed_types = FileUploadService.ALLOWED_CERTIFICATE_TYPES
            type_name = "Certificate"
        elif file_type == 'profile_picture':
            max_size = FileUploadService.MAX_PROFILE_PICTURE_SIZE
            allowed_types = FileUploadService.ALLOWED_PROFILE_PICTURE_TYPES
            type_name = "Profile Picture"
        else:
            return False, "Invalid file type"
        
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            return False, f"{type_name} must be less than {max_mb}MB"
        
        # Check MIME type
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        
        if mime_type not in allowed_types:
            allowed_exts = ', '.join(allowed_types.values())
            return False, f"{type_name} must be one of: {allowed_exts}"
        
        # Additional security: Check file extension matches MIME type
        file_ext = os.path.splitext(file.filename)[1].lower()
        expected_ext = allowed_types.get(mime_type)
        
        if file_ext != expected_ext:
            return False, f"File extension does not match file type"
        
        return True, None
    
    @staticmethod
    def generate_secure_filename(original_filename: str, user_id: int, file_type: str) -> str:
        """Generate a secure, unique filename"""
        ext = os.path.splitext(original_filename)[1].lower()
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return f"{file_type}_{user_id}_{timestamp}_{unique_id}{ext}"
    
    @staticmethod
    def save_file(file: FileStorage, user_id: int, file_type: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Save file to disk
        Returns: (success, error_message, file_info_dict)
        """
        # Validate file
        is_valid, error = FileUploadService.validate_file(file, file_type)
        if not is_valid:
            return False, error, None
        
        # Create user directory
        user_dir = os.path.join(FileUploadService.UPLOAD_BASE_DIR, 'professionals', str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Generate secure filename
        secure_fname = FileUploadService.generate_secure_filename(file.filename, user_id, file_type)
        file_path = os.path.join(user_dir, secure_fname)
        
        # Save file
        try:
            file.save(file_path)
        except Exception as e:
            return False, f"Failed to save file: {str(e)}", None
        
        # Get file info
        file_size = os.path.getsize(file_path)
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        
        # Calculate file hash for integrity verification
        file_hash = FileUploadService._calculate_file_hash(file_path)
        
        # Ensure web path uses forward slashes (not OS-specific backslashes)
        web_path = f'/static/uploads/professionals/{user_id}/{secure_fname}'
        
        file_info = {
            'file_name': secure_fname,
            'file_path': web_path,
            'absolute_path': file_path,
            'file_size': file_size,
            'mime_type': mime_type,
            'file_hash': file_hash,
            'original_name': file.filename
        }
        
        return True, None, file_info
    
    @staticmethod
    def delete_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Delete file from disk
        Returns: (success, error_message)
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True, None
            else:
                return False, "File not found"
        except Exception as e:
            return False, f"Failed to delete file: {str(e)}"
    
    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """Calculate SHA256 hash of file for integrity verification"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def verify_file_integrity(file_path: str, expected_hash: str) -> bool:
        """Verify file integrity using hash"""
        if not os.path.exists(file_path):
            return False
        current_hash = FileUploadService._calculate_file_hash(file_path)
        return current_hash == expected_hash
    
    @staticmethod
    def get_file_info(file_path: str) -> Optional[Dict]:
        """Get information about a file"""
        if not os.path.exists(file_path):
            return None
        
        file_size = os.path.getsize(file_path)
        mime_type = mimetypes.guess_type(file_path)[0]
        file_hash = FileUploadService._calculate_file_hash(file_path)
        
        return {
            'file_path': file_path,
            'file_size': file_size,
            'mime_type': mime_type,
            'file_hash': file_hash,
            'exists': True
        }
