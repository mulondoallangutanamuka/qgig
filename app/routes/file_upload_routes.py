"""
File Upload API Routes
Handles secure file uploads for professional profiles
"""
from flask import Blueprint, request, jsonify, session, send_file
from functools import wraps
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.professional import Professional
from app.models.document import Document, DocumentType, DocumentStatus
from app.services.file_upload_service import FileUploadService
from app.services.file_access_control import FileAccessControl
import os

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return wrapper

def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == session['user_id']).first()
                if not user or user.role.value != role:
                    return jsonify({'error': 'Forbidden'}), 403
                return f(*args, **kwargs)
            finally:
                db.close()
        return wrapper
    return decorator

# Create blueprint after decorators are defined
file_upload_blueprint = Blueprint('file_upload', __name__)

@file_upload_blueprint.route('/api/professional/upload-cv', methods=['POST'])
@login_required
@role_required('professional')
def upload_cv():
    """Upload CV for professional"""
    db = SessionLocal()
    try:
        # Get professional
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            return jsonify({'error': 'Professional profile not found'}), 404
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Save file using service
        success, error, file_info = FileUploadService.save_file(file, session['user_id'], 'cv')
        
        if not success:
            return jsonify({'error': error}), 400
        
        # Delete old CV if exists
        old_cv = db.query(Document).filter(
            Document.professional_id == professional.id,
            Document.document_type == DocumentType.CV
        ).first()
        
        if old_cv:
            # Delete old file from disk
            if os.path.exists(old_cv.file_path):
                FileUploadService.delete_file(old_cv.file_path)
            db.delete(old_cv)
        
        # Create document record
        document = Document(
            user_id=session['user_id'],
            professional_id=professional.id,
            document_type=DocumentType.CV,
            file_path=file_info['absolute_path'],
            file_name=file_info['file_name'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            status=DocumentStatus.PENDING
        )
        
        db.add(document)
        
        # Also update legacy field
        professional.cv_file = file_info['file_path']
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'CV uploaded successfully',
            'file': {
                'id': document.id,
                'name': file_info['file_name'],
                'size': file_info['file_size'],
                'url': file_info['file_path']
            }
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@file_upload_blueprint.route('/api/professional/upload-certificate', methods=['POST'])
@login_required
@role_required('professional')
def upload_certificate():
    """Upload certificate for professional"""
    db = SessionLocal()
    try:
        # Get professional
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            return jsonify({'error': 'Professional profile not found'}), 404
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Save file using service
        success, error, file_info = FileUploadService.save_file(file, session['user_id'], 'certificate')
        
        if not success:
            return jsonify({'error': error}), 400
        
        # Create document record
        document = Document(
            user_id=session['user_id'],
            professional_id=professional.id,
            document_type=DocumentType.CERTIFICATE,
            file_path=file_info['absolute_path'],
            file_name=file_info['file_name'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            status=DocumentStatus.PENDING
        )
        
        db.add(document)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Certificate uploaded successfully',
            'file': {
                'id': document.id,
                'name': file_info['file_name'],
                'size': file_info['file_size'],
                'url': file_info['file_path']
            }
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@file_upload_blueprint.route('/api/professional/upload-profile-picture', methods=['POST'])
@login_required
@role_required('professional')
def upload_profile_picture():
    """Upload profile picture for professional"""
    db = SessionLocal()
    try:
        # Get professional
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            return jsonify({'error': 'Professional profile not found'}), 404
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Save file using service
        success, error, file_info = FileUploadService.save_file(file, session['user_id'], 'profile_picture')
        
        if not success:
            return jsonify({'error': error}), 400
        
        # Delete old profile picture if exists
        old_pic = db.query(Document).filter(
            Document.professional_id == professional.id,
            Document.document_type == DocumentType.PROFILE_PICTURE
        ).first()
        
        if old_pic:
            # Delete old file from disk
            if os.path.exists(old_pic.file_path):
                FileUploadService.delete_file(old_pic.file_path)
            db.delete(old_pic)
        
        # Create document record
        document = Document(
            user_id=session['user_id'],
            professional_id=professional.id,
            document_type=DocumentType.PROFILE_PICTURE,
            file_path=file_info['absolute_path'],
            file_name=file_info['file_name'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            status=DocumentStatus.APPROVED
        )
        
        db.add(document)
        
        # Also update legacy field
        professional.profile_picture = file_info['file_path']
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile picture uploaded successfully',
            'file': {
                'id': document.id,
                'name': file_info['file_name'],
                'size': file_info['file_size'],
                'url': file_info['file_path']
            }
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@file_upload_blueprint.route('/api/professional/files', methods=['GET'])
@login_required
@role_required('professional')
def get_my_files():
    """Get list of uploaded files for current professional"""
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            return jsonify({'error': 'Professional profile not found'}), 404
        
        documents = db.query(Document).filter(Document.professional_id == professional.id).all()
        
        files = []
        for doc in documents:
            files.append({
                'id': doc.id,
                'type': doc.document_type.value,
                'name': doc.file_name,
                'size': doc.file_size,
                'uploaded_at': doc.uploaded_at.isoformat(),
                'status': doc.status.value
            })
        
        return jsonify({'files': files}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@file_upload_blueprint.route('/api/professional/files/<int:file_id>', methods=['DELETE'])
@login_required
@role_required('professional')
def delete_file(file_id):
    """Delete uploaded file"""
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            return jsonify({'error': 'Professional profile not found'}), 404
        
        document = db.query(Document).filter(
            Document.id == file_id,
            Document.professional_id == professional.id
        ).first()
        
        if not document:
            return jsonify({'error': 'File not found'}), 404
        
        # Delete file from disk
        if os.path.exists(document.file_path):
            FileUploadService.delete_file(document.file_path)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return jsonify({'success': True, 'message': 'File deleted successfully'}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@file_upload_blueprint.route('/api/professional/<int:professional_id>/download/<int:document_id>', methods=['GET'])
@login_required
def download_document(professional_id, document_id):
    """Download a document (with access control)"""
    db = SessionLocal()
    try:
        # Check access control
        can_access, reason = FileAccessControl.can_access_file(session['user_id'], document_id, db)
        
        if not can_access:
            return jsonify({'error': reason}), 403
        
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check if file exists
        if not os.path.exists(document.file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        # Log access
        FileAccessControl.log_file_access(session['user_id'], document_id, True, db)
        
        # Send file
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.file_name,
            mimetype=document.mime_type
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
