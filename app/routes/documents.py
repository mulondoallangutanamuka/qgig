from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app.database import SessionLocal
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.professional import Professional
from app.models.user import UserRole
from app.middleware.auth import token_required, role_required
from app.middleware.security import validate_file_upload, sanitize_filename, rate_limit
import os
from datetime import datetime

documents_blueprint = Blueprint("documents", __name__)

UPLOAD_FOLDER = "uploads/documents"
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@documents_blueprint.post("/upload")
@token_required
@role_required(UserRole.PROFESSIONAL)
def upload_document(current_user):
    db = SessionLocal()
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        document_type = request.form.get('document_type')
        
        if not document_type:
            return jsonify({"error": "Document type is required"}), 400
        
        try:
            doc_type = DocumentType[document_type.upper()]
        except KeyError:
            return jsonify({"error": "Invalid document type. Must be: nin, certificate, or license"}), 400
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed. Use PDF, JPG, or PNG"}), 400
        
        professional = db.query(Professional).filter(Professional.user_id == current_user.id).first()
        if not professional:
            return jsonify({"error": "Professional profile not found"}), 404
        
        # Sanitize and secure filename
        filename = sanitize_filename(file.filename)
        filename = secure_filename(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{current_user.id}_{doc_type.value}_{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(file_path)
        
        document = Document(
            user_id=current_user.id,
            document_type=doc_type,
            file_path=file_path,
            file_name=filename,
            status=DocumentStatus.PENDING
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return jsonify({
            "message": "Document uploaded successfully",
            "document": {
                "id": document.id,
                "type": document.document_type.value,
                "status": document.status.value,
                "uploaded_at": document.uploaded_at.isoformat()
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@documents_blueprint.get("/my-documents")
@token_required
@role_required(UserRole.PROFESSIONAL)
def get_my_documents(current_user):
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(Document.user_id == current_user.id).all()
        
        return jsonify({
            "documents": [{
                "id": doc.id,
                "type": doc.document_type.value,
                "file_name": doc.file_name,
                "status": doc.status.value,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "reviewed_at": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
                "admin_notes": doc.admin_notes
            } for doc in documents]
        }), 200
    finally:
        db.close()

@documents_blueprint.get("/pending")
@token_required
@role_required(UserRole.ADMIN)
def get_pending_documents(current_user):
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(Document.status == DocumentStatus.PENDING).all()
        
        return jsonify({
            "documents": [{
                "id": doc.id,
                "user_id": doc.user_id,
                "type": doc.document_type.value,
                "file_name": doc.file_name,
                "uploaded_at": doc.uploaded_at.isoformat()
            } for doc in documents]
        }), 200
    finally:
        db.close()

@documents_blueprint.put("/<int:document_id>/review")
@token_required
@role_required(UserRole.ADMIN)
def review_document(current_user, document_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return jsonify({"error": "Document not found"}), 404
        
        data = request.json
        status = data.get('status')
        
        if status not in ['approved', 'rejected']:
            return jsonify({"error": "Status must be 'approved' or 'rejected'"}), 400
        
        document.status = DocumentStatus[status.upper()]
        document.reviewed_at = datetime.utcnow()
        document.admin_notes = data.get('notes', '')
        
        db.commit()
        
        return jsonify({
            "message": f"Document {status}",
            "document": {
                "id": document.id,
                "status": document.status.value,
                "reviewed_at": document.reviewed_at.isoformat()
            }
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
