"""
Rating System Routes
Handles institution ratings for professionals after gig completion
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.job import Job, JobStatus
from app.models.rating import Rating
from sqlalchemy import func, desc

rating_routes_blueprint = Blueprint('rating_routes', __name__)

# Decorators
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == session['user_id']).first()
                if not user or user.role.value not in roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                return f(*args, **kwargs)
            finally:
                db.close()
        return wrapper
    return decorator

# Create blueprint after decorators are defined
rating_routes_blueprint = Blueprint('rating_routes', __name__)

@rating_routes_blueprint.route('/api/gigs/<int:gig_id>/rate', methods=['POST'])
@login_required
@role_required('institution')
def rate_professional(gig_id):
    """Institution rates professional after gig completion"""
    db = SessionLocal()
    try:
        # Get institution
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        # Get gig
        gig = db.query(Job).filter(Job.id == gig_id).first()
        if not gig:
            return jsonify({'error': 'Gig not found'}), 404
        
        # Verify institution owns this gig
        if gig.institution_id != institution.id:
            return jsonify({'error': 'You can only rate professionals for your own gigs'}), 403
        
        # Verify gig is completed
        if gig.status != JobStatus.COMPLETED:
            return jsonify({'error': 'You can only rate professionals after gig completion'}), 400
        
        # Verify gig has assigned professional
        if not gig.assigned_professional_id:
            return jsonify({'error': 'No professional assigned to this gig'}), 400
        
        # Check if already rated
        existing_rating = db.query(Rating).filter(
            Rating.gig_id == gig_id,
            Rating.rater_id == session['user_id']
        ).first()
        
        if existing_rating:
            return jsonify({'error': 'You have already rated this professional for this gig'}), 400
        
        # Get rating data
        data = request.get_json()
        rating_value = data.get('rating')
        feedback = data.get('feedback', '')
        
        # Validate rating
        if not rating_value or not isinstance(rating_value, (int, float)):
            return jsonify({'error': 'Rating is required'}), 400
        
        if rating_value < 1 or rating_value > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Get professional user_id
        professional = db.query(Professional).filter(Professional.id == gig.assigned_professional_id).first()
        if not professional:
            return jsonify({'error': 'Professional not found'}), 404
        
        # Create rating
        rating = Rating(
            gig_id=gig_id,
            institution_id=institution.id,
            professional_id=professional.id,
            rater_id=session['user_id'],
            rated_id=professional.user_id,
            rating=float(rating_value),
            feedback=feedback
        )
        
        db.add(rating)
        db.commit()
        
        # Send Socket.IO notification to professional
        try:
            from app import socketio
            socketio.emit('rating_submitted', {
                'message': f'{institution.name} has rated you {rating_value} stars',
                'gig_title': gig.title,
                'rating': rating_value
            }, room=f'user_{professional.user_id}')
        except:
            pass  # Don't fail if Socket.IO fails
        
        return jsonify({
            'success': True,
            'message': 'Rating submitted successfully',
            'rating': {
                'id': rating.id,
                'rating': rating.rating,
                'feedback': rating.feedback
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@rating_routes_blueprint.route('/api/professional/<int:professional_id>/ratings', methods=['GET'])
@login_required
def get_professional_ratings(professional_id):
    """Get ratings for a professional"""
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.id == professional_id).first()
        if not professional:
            return jsonify({'error': 'Professional not found'}), 404
        
        # Get all ratings
        ratings = db.query(Rating).filter(Rating.professional_id == professional_id).order_by(desc(Rating.created_at)).all()
        
        # Calculate average
        avg_rating = db.query(func.avg(Rating.rating)).filter(Rating.professional_id == professional_id).scalar() or 0
        
        # Format ratings
        ratings_list = []
        for r in ratings:
            institution = db.query(Institution).filter(Institution.id == r.institution_id).first()
            ratings_list.append({
                'id': r.id,
                'rating': r.rating,
                'feedback': r.feedback,
                'institution_name': institution.name if institution else 'Unknown',
                'created_at': r.created_at.isoformat()
            })
        
        return jsonify({
            'average_rating': round(float(avg_rating), 2),
            'total_ratings': len(ratings),
            'ratings': ratings_list[:5]  # Return last 5 ratings
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@rating_routes_blueprint.route('/api/professional/<int:professional_id>/rating-summary', methods=['GET'])
def get_rating_summary(professional_id):
    """Get rating summary for a professional (public endpoint)"""
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.id == professional_id).first()
        if not professional:
            return jsonify({'error': 'Professional not found'}), 404
        
        # Calculate average rating
        avg_rating = db.query(func.avg(Rating.rating)).filter(Rating.professional_id == professional_id).scalar() or 0
        
        # Count total ratings
        total_ratings = db.query(func.count(Rating.id)).filter(Rating.professional_id == professional_id).scalar() or 0
        
        # Get rating distribution
        rating_distribution = {}
        for i in range(1, 6):
            count = db.query(func.count(Rating.id)).filter(
                Rating.professional_id == professional_id,
                Rating.rating >= i,
                Rating.rating < i + 1
            ).scalar() or 0
            rating_distribution[str(i)] = count
        
        return jsonify({
            'average_rating': round(float(avg_rating), 2),
            'total_ratings': total_ratings,
            'rating_distribution': rating_distribution
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@rating_routes_blueprint.route('/api/gigs/<int:gig_id>/can-rate', methods=['GET'])
@login_required
@role_required('institution')
def can_rate_gig(gig_id):
    """Check if institution can rate this gig"""
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'can_rate': False, 'reason': 'Institution profile not found'}), 200
        
        gig = db.query(Job).filter(Job.id == gig_id).first()
        if not gig:
            return jsonify({'can_rate': False, 'reason': 'Gig not found'}), 200
        
        if gig.institution_id != institution.id:
            return jsonify({'can_rate': False, 'reason': 'Not your gig'}), 200
        
        if gig.status != JobStatus.COMPLETED:
            return jsonify({'can_rate': False, 'reason': 'Gig not completed'}), 200
        
        # Check if already rated
        existing_rating = db.query(Rating).filter(
            Rating.gig_id == gig_id,
            Rating.rater_id == session['user_id']
        ).first()
        
        if existing_rating:
            return jsonify({'can_rate': False, 'reason': 'Already rated'}), 200
        
        return jsonify({'can_rate': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
