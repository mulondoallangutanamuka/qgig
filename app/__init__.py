from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_login import LoginManager
from app.database import Base, engine, SessionLocal
from app.routes.auth import auth_blueprint
from app.routes.payments import payments_blueprint
from app.routes.health import health_blueprint
from app.routes.professional import professional_blueprint
from app.routes.institution import institution_blueprint
from app.routes.documents import documents_blueprint
from app.routes.jobs import jobs_blueprint
from app.routes.ratings import ratings_blueprint
from app.routes.admin import admin_blueprint
from app.routes.web import web_blueprint
from app.routes.analytics import analytics_blueprint
from app.routes.file_upload_routes import file_upload_blueprint
from app.routes.messages import messages_blueprint
# from app.routes.rating_routes import rating_routes_blueprint
import os

# Global SocketIO instance
socketio = None

def create_app():
    global socketio
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static',
                static_url_path='/static')
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    CORS(app, supports_credentials=True)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'web.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            return user
        finally:
            db.close()
    
    # Initialize SocketIO with session support
    socketio = SocketIO(app, 
                       cors_allowed_origins="*", 
                       manage_session=True,
                       async_mode='threading',
                       logger=True,
                       engineio_logger=True)

    # Register blueprints
    # Web routes (Jinja templates) - no prefix
    app.register_blueprint(web_blueprint)
    
    # API routes
    app.register_blueprint(health_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
    app.register_blueprint(payments_blueprint, url_prefix="/api/payments")
    app.register_blueprint(professional_blueprint, url_prefix="/api/professional")
    app.register_blueprint(institution_blueprint, url_prefix="/api/institution")
    app.register_blueprint(documents_blueprint, url_prefix="/api/documents")
    app.register_blueprint(jobs_blueprint, url_prefix="/api/jobs")
    app.register_blueprint(ratings_blueprint, url_prefix="/api/ratings")
    app.register_blueprint(admin_blueprint, url_prefix="/api/admin")
    app.register_blueprint(analytics_blueprint, url_prefix="/api/analytics")
    app.register_blueprint(file_upload_blueprint)
    app.register_blueprint(messages_blueprint)
    # app.register_blueprint(rating_routes_blueprint)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found", "status": 404}), 404

    @app.errorhandler(500)
    def internal_error(error):
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({"error": "Internal server error", "status": 500}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        
        # Don't expose internal errors in production
        if app.debug:
            return jsonify({"error": str(error), "status": 500}), 500
        else:
            return jsonify({"error": "An unexpected error occurred", "status": 500}), 500

    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Import and register socket events (must be after socketio initialization)
    from app.sockets import register_socketio_events, set_socketio
    set_socketio(socketio)
    register_socketio_events(socketio)

    return app, socketio
