"""
Route for serving uploaded files
Handles document downloads with proper error handling
"""
from flask import Blueprint, send_from_directory, abort, current_app
import os

file_serve_blueprint = Blueprint('file_serve', __name__)

@file_serve_blueprint.route('/static/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files from the uploads directory"""
    try:
        # Get the absolute path to the uploads directory
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        uploads_dir = os.path.join(app_dir, 'static', 'uploads')
        
        # Ensure uploads directory exists
        if not os.path.exists(uploads_dir):
            print(f"Uploads directory not found: {uploads_dir}")
            abort(404)
        
        # Full file path
        file_path = os.path.join(uploads_dir, filename)
        
        # Security check - prevent directory traversal
        real_path = os.path.realpath(file_path)
        real_uploads = os.path.realpath(uploads_dir)
        
        if not real_path.startswith(real_uploads):
            print(f"Security: Path traversal attempt blocked: {filename}")
            abort(403)
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            abort(404)
        
        # Serve the file with proper mimetype
        return send_from_directory(uploads_dir, filename, as_attachment=True)
        
    except Exception as e:
        print(f"Error serving file {filename}: {str(e)}")
        import traceback
        traceback.print_exc()
        abort(500)
