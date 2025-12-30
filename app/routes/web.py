"""
Web routes for rendering Jinja templates
Handles all page rendering and form submissions for the web UI
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, current_app
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.job import Job, JobStatus, GigInterest
from app.models.payment import Payment, TransactionStatus
from app.models.rating import Rating
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.notification import Notification
from app.models.job_interest import JobInterest, InterestStatus
from app.models.message import Message
from sqlalchemy import func, or_, desc, asc
from sqlalchemy.orm import joinedload
from functools import wraps
import bcrypt
from datetime import datetime, timedelta
import os
import secrets
import hashlib
import smtplib
import ssl
from email.message import EmailMessage
import logging
from werkzeug.utils import secure_filename
from app.services.file_upload_service import FileUploadService
from app.services.file_access_control import FileAccessControl

web_blueprint = Blueprint('web', __name__)

# Helper function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def _send_email(to_email: str, subject: str, body: str) -> bool:
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER') or os.getenv('SENDER_MAIL')
    smtp_password = os.getenv('SMTP_PASSWORD') or os.getenv('PASSWORD')
    smtp_from = os.getenv('SMTP_FROM') or smtp_user
    use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() in ['1', 'true', 'yes', 'on']
    use_ssl = os.getenv('SMTP_USE_SSL', 'false').lower() in ['1', 'true', 'yes', 'on']

    if not smtp_host or not smtp_from:
        logging.getLogger(__name__).warning(
            "SMTP not configured; missing SMTP_HOST or sender. SMTP_HOST=%s SMTP_FROM=%s", 
            smtp_host, 
            smtp_from
        )
        return False

    if smtp_user and not smtp_password:
        logging.getLogger(__name__).warning(
            "SMTP missing password for user=%s (set SMTP_PASSWORD or PASSWORD)",
            smtp_user
        )
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = smtp_from
    msg['To'] = to_email
    msg.set_content(body)

    logging.getLogger(__name__).info(
        "SMTP send attempt host=%s port=%s to=%s ssl=%s tls=%s from=%s user=%s",
        smtp_host,
        smtp_port,
        to_email,
        use_ssl,
        use_tls,
        smtp_from,
        smtp_user
    )

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            logging.getLogger(__name__).info("SMTP email sent to=%s subject=%s", to_email, subject)
            return True

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logging.getLogger(__name__).info("SMTP email sent to=%s subject=%s", to_email, subject)
        return True
    except Exception as e:
        logging.getLogger(__name__).warning(
            "SMTP send failed (host=%s port=%s to=%s ssl=%s tls=%s): %s",
            smtp_host,
            smtp_port,
            to_email,
            use_ssl,
            use_tls,
            str(e)
        )
        return False

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            is_ajax = (
                request.is_json or
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                'application/json' in (request.headers.get('Accept') or '') or
                request.path.startswith('/settings/')
            )
            if is_ajax:
                return jsonify({'error': 'Unauthorized. Please log in again.'}), 401

            flash('Please login to access this page', 'warning')
            return redirect(url_for('web.login'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                is_ajax = (
                    request.is_json or
                    request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                    'application/json' in (request.headers.get('Accept') or '') or
                    request.path.startswith('/settings/')
                )
                if is_ajax:
                    return jsonify({'error': 'Unauthorized. Please log in again.'}), 401

                flash('Please login to access this page', 'warning')
                return redirect(url_for('web.login'))
            
            db = SessionLocal()
            user = db.query(User).filter(User.id == session['user_id']).first()
            db.close()

            active_role = session.get('active_role') or session.get('role') or session.get('user_role')
            if user and active_role and active_role not in roles:
                is_ajax = (
                    request.is_json or
                    request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                    'application/json' in (request.headers.get('Accept') or '') or
                    request.path.startswith('/settings/')
                )
                if is_ajax:
                    return jsonify({'error': 'Forbidden'}), 403

                flash('You do not have permission to access this page', 'error')
                return redirect(url_for('web.home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Context processor to inject current user into all templates
@web_blueprint.context_processor
def inject_user():
    current_user = None
    unread_count = 0
    notification_count = 0
    role_stats = {}
    active_role = None
    is_verified = False
    completed_gigs_list = []
    cv_boost = {}
    
    if 'user_id' in session:
        db = SessionLocal()
        current_user = db.query(User).filter(User.id == session['user_id']).first()
        
        # Get active role
        active_role = session.get('active_role', current_user.role.value if current_user else None)
        
        # Get unread notification count filtered by active role
        notification_count = db.query(Notification).filter(
            Notification.user_id == session['user_id'],
            Notification.is_read == False,
            or_(
                Notification.role_context == active_role,
                Notification.role_context == None  # Include notifications for all roles
            )
        ).count()
        unread_count = notification_count
        
        # Get role-specific data and profile picture
        if current_user:
            # Get professional profile
            prof = db.query(Professional).filter(Professional.user_id == current_user.id).first()
            if prof:
                # Try to get profile picture from Document table first
                profile_pic = db.query(Document).filter(
                    Document.professional_id == prof.id,
                    Document.document_type == DocumentType.PROFILE_PICTURE
                ).first()
                # Fall back to legacy field if Document doesn't exist
                current_user.profile_picture = profile_pic.file_path if profile_pic else prof.profile_picture

                requires_registration = (prof.profession_category in ['Health', 'Formal']) if prof.profession_category else False
                is_verified = bool(requires_registration and prof.registration_number and prof.issuing_body)
            else:
                current_user.profile_picture = None
            
            # Get institution profile
            inst = db.query(Institution).filter(Institution.user_id == current_user.id).first()
            
            # Collect role-specific stats based on active role
            if active_role == 'professional' and prof:
                # Professional stats
                interested_gigs = db.query(GigInterest).filter(
                    GigInterest.professional_id == prof.id
                ).count()
                
                assigned_gigs = db.query(Job).filter(
                    Job.assigned_professional_id == prof.id,
                    Job.status == JobStatus.ASSIGNED
                ).count()
                
                completed_gigs = db.query(Job).filter(
                    Job.assigned_professional_id == prof.id,
                    Job.status == JobStatus.COMPLETED
                ).count()
                
                total_earned = db.query(func.sum(Payment.amount)).filter(
                    Payment.professional_id == prof.id,
                    Payment.status == TransactionStatus.COMPLETED
                ).scalar() or 0
                
                completed_gigs_list = db.query(Job).options(
                    joinedload(Job.institution)
                ).filter(
                    Job.assigned_professional_id == prof.id,
                    Job.status == JobStatus.COMPLETED
                ).order_by(desc(Job.updated_at)).limit(10).all()

                average_rating, total_ratings = db.query(
                    func.avg(Rating.rating),
                    func.count(Rating.id)
                ).filter(Rating.professional_id == prof.id).first()

                repeat_clients = db.query(func.count(func.distinct(Job.institution_id))).filter(
                    Job.assigned_professional_id == prof.id,
                    Job.status == JobStatus.COMPLETED
                ).scalar() or 0

                top_sectors = db.query(Job.sector, func.count(Job.id)).filter(
                    Job.assigned_professional_id == prof.id,
                    Job.status == JobStatus.COMPLETED,
                    Job.sector.isnot(None),
                    Job.sector != ''
                ).group_by(Job.sector).order_by(desc(func.count(Job.id))).limit(3).all()

                top_job_types = db.query(Job.job_type, func.count(Job.id)).filter(
                    Job.assigned_professional_id == prof.id,
                    Job.status == JobStatus.COMPLETED,
                    Job.job_type.isnot(None),
                    Job.job_type != ''
                ).group_by(Job.job_type).order_by(desc(func.count(Job.id))).limit(3).all()

                total_hours = db.query(func.sum(Job.duration_hours)).filter(
                    Job.assigned_professional_id == prof.id,
                    Job.status == JobStatus.COMPLETED
                ).scalar() or 0

                cv_boost = {
                    'average_rating': float(average_rating) if average_rating is not None else 0,
                    'total_ratings': int(total_ratings or 0),
                    'repeat_clients': int(repeat_clients),
                    'top_sectors': [{'name': s, 'count': int(c)} for s, c in top_sectors],
                    'top_job_types': [{'name': t, 'count': int(c)} for t, c in top_job_types],
                    'total_hours': float(total_hours or 0)
                }
                
                role_stats = {
                    'interested_gigs': interested_gigs,
                    'assigned_gigs': assigned_gigs,
                    'completed_gigs': completed_gigs,
                    'total_earned': total_earned,
                    'profile_completion': _calculate_profile_completion(prof)
                }
                
            elif active_role == 'institution' and inst:
                # Institution stats
                open_gigs = db.query(Job).filter(
                    Job.institution_id == inst.id,
                    Job.status == JobStatus.OPEN
                ).count()
                
                assigned_gigs = db.query(Job).filter(
                    Job.institution_id == inst.id,
                    Job.status == JobStatus.ASSIGNED
                ).count()
                
                completed_gigs = db.query(Job).filter(
                    Job.institution_id == inst.id,
                    Job.status == JobStatus.COMPLETED
                ).count()
                
                pending_interests = db.query(GigInterest).join(Job).filter(
                    Job.institution_id == inst.id,
                    Job.status == JobStatus.OPEN
                ).count()
                
                total_spent = db.query(func.sum(Payment.amount)).filter(
                    Payment.institution_id == inst.id,
                    Payment.status == TransactionStatus.COMPLETED
                ).scalar() or 0
                
                role_stats = {
                    'open_gigs': open_gigs,
                    'assigned_gigs': assigned_gigs,
                    'completed_gigs': completed_gigs,
                    'pending_interests': pending_interests,
                    'total_spent': total_spent,
                    'profile_completion': _calculate_institution_profile_completion(inst)
                }
        
        db.close()
    
    return dict(
        current_user=current_user,
        unread_count=unread_count,
        notification_count=notification_count,
        active_role=active_role,
        role_stats=role_stats,
        is_verified=is_verified,
        completed_gigs_list=completed_gigs_list,
        cv_boost=cv_boost
    )


def _calculate_profile_completion(prof):
    """Calculate professional profile completion percentage"""
    fields = [
        prof.full_name,
        prof.phone_number,
        prof.skills,
        prof.bio,
        prof.location,
        prof.hourly_rate or prof.daily_rate,
        prof.education,
        prof.experience
    ]
    completed = sum(1 for field in fields if field)
    return int((completed / len(fields)) * 100)


def _calculate_institution_profile_completion(inst):
    """Calculate institution profile completion percentage"""
    fields = [
        inst.institution_name,
        inst.description,
        inst.contact_email,
        inst.contact_phone,
        inst.location
    ]
    completed = sum(1 for field in fields if field)
    return int((completed / len(fields)) * 100)

# ===== Authentication Routes =====

@web_blueprint.route('/test-chat')
def test_chat():
    """Test page for chat opening functionality"""
    return send_from_directory('..', 'test_chat_opening.html')

@web_blueprint.route('/')
def home():
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    
    try:
        # Get recent gigs with eagerly loaded institution, excluding expired ones
        recent_gigs = db.query(Job).options(joinedload(Job.institution)).filter(
            Job.status == JobStatus.OPEN
        ).filter(
            (Job.expiry_date == None) | (Job.expiry_date > datetime.utcnow())
        ).order_by(desc(Job.created_at)).limit(6).all()
        
        # Add interest count to each gig
        for gig in recent_gigs:
            gig.interest_count = db.query(JobInterest).filter(JobInterest.job_id == gig.id).count()
        
        # Get stats
        stats = {
            'total_gigs': db.query(Job).count(),
            'total_professionals': db.query(Professional).count(),
            'completed_gigs': db.query(Job).filter(Job.status == JobStatus.COMPLETED).count(),
            'total_paid': db.query(func.sum(Payment.amount)).filter(Payment.status == TransactionStatus.COMPLETED).scalar() or 0
        }
        
        return render_template('home.html', recent_gigs=recent_gigs, stats=stats)
    finally:
        db.close()


@web_blueprint.route('/professional/<int:professional_id>')
@login_required
@role_required('professional', 'institution')
def professional_profile_view(professional_id):
    """View a professional profile (role-aware redirect)."""
    active_role = session.get('active_role')
    
    # Institutions view professionals via the institution dashboard history view
    if active_role == 'institution':
        return redirect(url_for('web.professional_history', professional_id=professional_id))

    # Professionals can only view their own profile via /profile
    if active_role == 'professional':
        db = SessionLocal()
        try:
            professional = db.query(Professional).filter(Professional.id == professional_id).first()
            if not professional:
                flash('Professional not found', 'error')
                return redirect(url_for('web.profile'))

            if professional.user_id != session.get('user_id'):
                from flask import abort
                abort(403)

            return redirect(url_for('web.profile'))
        finally:
            db.close()

    from flask import abort
    abort(403)

@web_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        
        if user and verify_password(password, user.password):
            if not user.is_active:
                flash('Your account has been suspended. Please contact support.', 'error')
                db.close()
                return redirect(url_for('web.login'))
            
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_role'] = user.role.value
            session['active_role'] = user.role.value
            
            flash(f'Welcome back, {email.split("@")[0]}!', 'success')
            db.close()
            
            # Redirect based on active_role (not user.role)
            active_role = session.get('active_role', user.role.value)
            if active_role == 'admin':
                return redirect(url_for('web.admin_dashboard'))
            else:
                # Use unified dashboard for professional and institution roles
                return redirect(url_for('web.dashboard'))
        else:
            flash('Invalid email or password', 'error')
            db.close()
    
    return render_template('login.html')

@web_blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('web.signup'))
        
        db = SessionLocal()
        
        try:
            # Check if user exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                flash('Email already registered', 'error')
                db.close()
                return redirect(url_for('web.signup'))
            
            # Create user with default professional role (for backward compatibility)
            user = User(
                email=email,
                password=hash_password(password),
                role=UserRole.PROFESSIONAL,
                is_active=True
            )
            db.add(user)
            db.flush()
            
            # Create BOTH profiles (multi-role support)
            professional_profile = Professional(user_id=user.id)
            institution_profile = Institution(user_id=user.id)
            db.add(professional_profile)
            db.add(institution_profile)
            db.flush()
            
            # Bootstrap into new roles tables
            from app.models.role import Role, UserRoleAssignment
            
            # Ensure professional and institution roles exist
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
            
            flash('Account created successfully! You can switch between Professional and Institution roles after login.', 'success')
            db.close()
            
            return redirect(url_for('web.login'))
        except Exception as e:
            db.rollback()
            flash(f'Error creating account: {str(e)}', 'error')
            db.close()
            return redirect(url_for('web.signup'))
    
    return render_template('signup.html')

@web_blueprint.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('web.home'))

@web_blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()

            # Always show the same message to avoid leaking whether an email exists
            flash('If an account exists for that email, a reset link has been sent.', 'success')

            if user and user.is_active:
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256((token + current_app.secret_key).encode('utf-8')).hexdigest()
                user.password_reset_token_hash = token_hash
                user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
                db.commit()

                reset_url = url_for('web.reset_password', token=token, _external=True)
                email_subject = 'Reset your QGig password'
                email_body = (
                    'We received a request to reset your password.\n\n'
                    f'Reset link: {reset_url}\n\n'
                    'This link expires in 1 hour. If you did not request this, you can ignore this email.'
                )

                sent = _send_email(email, email_subject, email_body)
                if not sent:
                    current_app.logger.info(f"Password reset link for {email}: {reset_url}")
        finally:
            db.close()

        return redirect(url_for('web.login'))
    
    return render_template('forgot_password.html')


@web_blueprint.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    token_hash = hashlib.sha256((token + current_app.secret_key).encode('utf-8')).hexdigest()

    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.password_reset_token_hash == token_hash,
            User.password_reset_expires_at != None,
            User.password_reset_expires_at > datetime.utcnow()
        ).first()

        if not user:
            flash('This reset link is invalid or has expired.', 'error')
            return redirect(url_for('web.forgot_password'))

        if request.method == 'POST':
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not new_password:
                flash('Password is required.', 'error')
                return render_template('reset_password.html', token=token)

            if new_password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('reset_password.html', token=token)

            user.password = hash_password(new_password)
            user.password_reset_token_hash = None
            user.password_reset_expires_at = None
            user.updated_at = datetime.utcnow()
            db.commit()

            flash('Your password has been reset. You can now log in.', 'success')
            return redirect(url_for('web.login'))

        return render_template('reset_password.html', token=token)
    finally:
        db.close()

# ===== Gig Routes =====

@web_blueprint.route('/gigs')
def browse_gigs():
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    
    try:
        # Get filter parameters
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        location = request.args.get('location', '')
        job_type = request.args.get('job_type', '')
        sector = request.args.get('sector', '')
        sort = request.args.get('sort', 'newest')
        urgent = request.args.get('urgent', '')
        page = int(request.args.get('page', 1))
        per_page = 12
        
        # Build query with eager loading, excluding expired gigs
        query = db.query(Job).options(joinedload(Job.institution))
        
        # Filter out expired gigs
        query = query.filter(
            (Job.expiry_date == None) | (Job.expiry_date > datetime.utcnow())
        )
        
        if search:
            query = query.filter(or_(
                Job.title.ilike(f'%{search}%'),
                Job.description.ilike(f'%{search}%'),
                Job.location.ilike(f'%{search}%')
            ))
        
        if status:
            query = query.filter(Job.status == JobStatus[status.upper()])
        
        if location:
            query = query.filter(Job.location == location)
        
        if job_type:
            query = query.filter(Job.job_type == job_type)
        
        if sector:
            query = query.filter(Job.sector == sector)
        
        if urgent:
            query = query.filter(Job.is_urgent == True)
        
        # Sorting
        if sort == 'newest':
            query = query.order_by(desc(Job.created_at))
        elif sort == 'oldest':
            query = query.order_by(asc(Job.created_at))
        elif sort == 'price_high':
            query = query.order_by(desc(Job.pay_amount))
        elif sort == 'price_low':
            query = query.order_by(asc(Job.pay_amount))
        
        # Pagination
        total = query.count()
        gigs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Add interest count and check if user has interest
        professional_id = None
        if 'user_id' in session:
            user = db.query(User).filter(User.id == session['user_id']).first()
            if user and user.role == UserRole.PROFESSIONAL:
                professional = db.query(Professional).filter(Professional.user_id == user.id).first()
                if professional:
                    professional_id = professional.id
        
        for gig in gigs:
            gig.interest_count = db.query(JobInterest).filter(JobInterest.job_id == gig.id).count()
            gig.user_has_interest = False
            if professional_id:
                existing_interest = db.query(JobInterest).filter(
                    JobInterest.job_id == gig.id,
                    JobInterest.professional_id == professional_id
                ).first()
                gig.user_has_interest = existing_interest is not None
        
        # Get unique locations for filter
        locations = db.query(Job.location).distinct().all()
        locations = [loc[0] for loc in locations]
        
        # Pagination object
        class Pagination:
            def __init__(self, page, per_page, total):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1
                self.next_num = page + 1
            
            def iter_pages(self):
                for i in range(1, self.pages + 1):
                    yield i
        
        pagination = Pagination(page, per_page, total)
        
        return render_template('browse_gigs.html', gigs=gigs, locations=locations, pagination=pagination)
    finally:
        db.close()

@web_blueprint.route('/gigs/<int:gig_id>')
def gig_detail(gig_id):
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    
    try:
        gig = db.query(Job).options(
            joinedload(Job.institution),
            joinedload(Job.ratings)
        ).filter(Job.id == gig_id).first()
        
        if not gig:
            flash('Gig not found', 'error')
            return redirect(url_for('web.browse_gigs'))
        
        gig.interest_count = db.query(JobInterest).filter(JobInterest.job_id == gig.id).count()
        
        # Check if current user has already shown interest
        user_has_interest = False
        if 'user_id' in session:
            user = db.query(User).filter(User.id == session['user_id']).first()
            if user and user.role == UserRole.PROFESSIONAL:
                professional = db.query(Professional).filter(Professional.user_id == user.id).first()
                if professional:
                    existing_interest = db.query(JobInterest).filter(
                        JobInterest.job_id == gig_id,
                        JobInterest.professional_id == professional.id
                    ).first()
                    user_has_interest = existing_interest is not None
        
        return render_template('gig_detail.html', gig=gig, user_has_interest=user_has_interest)
    finally:
        db.close()

@web_blueprint.route('/gigs/post', methods=['GET', 'POST'])
@login_required
@role_required('institution')
def post_gig():
    if request.method == 'POST':
        db = SessionLocal()
        
        # Get institution
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        
        if not institution:
            flash('Please complete your institution profile first', 'warning')
            db.close()
            return redirect(url_for('web.profile'))
        
        # Handle expiry date for urgent gigs
        expiry_date = None
        if request.form.get('is_urgent') and request.form.get('expiry_date'):
            expiry_date = datetime.fromisoformat(request.form.get('expiry_date'))
        
        # Create gig
        gig = Job(
            institution_id=institution.id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            location=request.form.get('location'),
            job_type=request.form.get('job_type'),
            sector=request.form.get('sector'),
            pay_amount=float(request.form.get('pay_amount')),
            duration_hours=float(request.form.get('duration_hours')) if request.form.get('duration_hours') else None,
            is_urgent=bool(request.form.get('is_urgent')),
            expiry_date=expiry_date,
            status=JobStatus.OPEN
        )
        
        db.add(gig)
        db.commit()
        
        flash('Gig posted successfully!', 'success')
        db.close()
        
        return redirect(url_for('web.my_gigs'))
    
    return render_template('post_gig.html')

@web_blueprint.route('/gigs/my-gigs')
@login_required
@role_required('institution')
def my_gigs():
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        
        if not institution:
            flash('Please complete your institution profile first', 'warning')
            return redirect(url_for('web.profile'))
        
        gigs = db.query(Job).options(
            joinedload(Job.assigned_professional).joinedload(Professional.user)
        ).filter(Job.institution_id == institution.id).order_by(desc(Job.created_at)).all()
        
        # Add interest count and payment status
        for gig in gigs:
            gig.interest_count = db.query(JobInterest).filter(JobInterest.job_id == gig.id).count()
            
            # Check payment status
            payment = db.query(Payment).filter(Payment.gig_id == gig.id).first()
            if payment:
                gig.payment_status = payment.status.value
            else:
                gig.payment_status = None
        
        # Stats
        stats = {
            'total': len(gigs),
            'open': len([g for g in gigs if g.status == JobStatus.OPEN]),
            'assigned': len([g for g in gigs if g.status == JobStatus.ASSIGNED]),
            'completed': len([g for g in gigs if g.status == JobStatus.COMPLETED])
        }
        
        return render_template('my_gigs.html', gigs=gigs, stats=stats)
    finally:
        db.close()

@web_blueprint.route('/jobs/<int:gig_id>/complete', methods=['POST'])
@login_required
@role_required('institution')
def complete_gig(gig_id):
    """Institution marks a gig as completed (session-based auth)"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            return jsonify({'error': 'Gig not found or unauthorized'}), 403
        
        if gig.status == JobStatus.COMPLETED:
            return jsonify({'error': 'Gig is already completed'}), 400
        
        if gig.status != JobStatus.ASSIGNED:
            return jsonify({'error': 'Only assigned gigs can be marked as completed'}), 400
        
        if not gig.assigned_professional_id:
            return jsonify({'error': 'No professional assigned to this gig'}), 400
        
        gig.status = JobStatus.COMPLETED
        gig.updated_at = datetime.utcnow()
        db.commit()
        
        # Notify the professional
        from app import socketio
        professional = db.query(Professional).filter(Professional.id == gig.assigned_professional_id).first()
        if professional:
            socketio.emit('notification', {
                'message': f'Gig "{gig.title}" has been marked as completed! Payment pending.',
                'type': 'success'
            }, room=f'user_{professional.user_id}')
        
        return jsonify({'message': 'Gig marked as completed successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/jobs/<int:gig_id>/initiate-payment', methods=['POST'])
@login_required
@role_required('institution')
def initiate_payment_web(gig_id):
    """Institution initiates payment for a gig (session-based auth)"""
    from flask import jsonify
    from app.services.pesapal import PesaPal
    from app.models.payment import Payment, TransactionStatus
    import uuid
    
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            return jsonify({'error': 'Gig not found or unauthorized'}), 403
        
        if gig.status not in [JobStatus.ASSIGNED, JobStatus.COMPLETED]:
            return jsonify({'error': 'Gig must be assigned or completed before payment'}), 400
        
        if not gig.assigned_professional_id:
            return jsonify({'error': 'No professional assigned to this gig'}), 400
        
        # Check if payment already exists
        existing_payment = db.query(Payment).filter(
            Payment.gig_id == gig.id,
            Payment.status == TransactionStatus.COMPLETED
        ).first()
        
        if existing_payment:
            return jsonify({'error': 'Payment already completed for this gig'}), 400
        
        professional = db.query(Professional).filter(Professional.id == gig.assigned_professional_id).first()
        if not professional:
            return jsonify({'error': 'Professional not found'}), 404
        
        professional_user = db.query(User).filter(User.id == professional.user_id).first()
        user = db.query(User).filter(User.id == session['user_id']).first()
        
        # Use professional's phone number for payment
        professional_phone = professional.phone_number or "0700000000"
        
        merchant_reference = f"QGIG-{uuid.uuid4().hex[:12].upper()}"
        
        payment = Payment(
            gig_id=gig.id,
            institution_id=institution.id,
            professional_id=professional.id,
            amount=gig.pay_amount,
            pesapal_merchant_reference=merchant_reference,
            status=TransactionStatus.PENDING
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        pesapal = PesaPal()
        
        try:
            response = pesapal.initiate_payment(
                amount=gig.pay_amount,
                email=professional_user.email,
                phone=professional_phone,
                merchant_reference=merchant_reference
            )
            
            payment.pesapal_order_tracking_id = response.get('order_tracking_id')
            db.commit()
            
            return jsonify({
                'message': 'Payment initiated successfully',
                'payment_id': payment.id,
                'redirect_url': response.get('redirect_url'),
                'order_tracking_id': response.get('order_tracking_id')
            }), 201
            
        except Exception as e:
            payment.status = TransactionStatus.FAILED
            db.commit()
            return jsonify({'error': f'Payment initiation failed: {str(e)}'}), 500
            
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/jobs/<int:gig_id>/retry-payment', methods=['POST'])
@login_required
@role_required('institution')
def retry_payment_web(gig_id):
    """Retry payment for a gig with pending payment (session-based auth)"""
    from flask import jsonify
    from app.services.pesapal import PesaPal
    from app.models.payment import Payment, TransactionStatus
    import uuid
    
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            return jsonify({'error': 'Gig not found or unauthorized'}), 403
        
        # Get existing pending payment
        payment = db.query(Payment).filter(
            Payment.gig_id == gig.id,
            Payment.status == TransactionStatus.PENDING
        ).order_by(Payment.created_at.desc()).first()
        
        if not payment:
            return jsonify({'error': 'No pending payment found for this gig'}), 404
        
        # Get professional details for payment
        professional = db.query(Professional).filter(Professional.id == gig.assigned_professional_id).first()
        if not professional:
            return jsonify({'error': 'Professional not found'}), 404
        
        professional_user = db.query(User).filter(User.id == professional.user_id).first()
        user = db.query(User).filter(User.id == session['user_id']).first()
        
        # Use professional's phone number for payment
        professional_phone = professional.phone_number or "0700000000"
        
        # Generate new merchant reference for retry
        merchant_reference = f"QGIG-{uuid.uuid4().hex[:12].upper()}"
        payment.pesapal_merchant_reference = merchant_reference
        
        pesapal = PesaPal()
        
        try:
            response = pesapal.initiate_payment(
                amount=gig.pay_amount,
                email=professional_user.email,
                phone=professional_phone,
                merchant_reference=merchant_reference
            )
            
            payment.pesapal_order_tracking_id = response.get('order_tracking_id')
            payment.updated_at = datetime.utcnow()
            db.commit()
            
            return jsonify({
                'message': 'Payment retry initiated successfully',
                'payment_id': payment.id,
                'redirect_url': response.get('redirect_url'),
                'order_tracking_id': response.get('order_tracking_id')
            }), 201
            
        except Exception as e:
            payment.status = TransactionStatus.FAILED
            db.commit()
            return jsonify({'error': f'Payment retry failed: {str(e)}'}), 500
            
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/jobs/<int:gig_id>/payment-status', methods=['GET'])
@login_required
@role_required('institution')
def check_payment_status_web(gig_id):
    """Check payment status for a gig (session-based auth)"""
    from flask import jsonify
    from app.services.pesapal import PesaPal
    from app.models.payment import Payment, TransactionStatus
    
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            return jsonify({'error': 'Gig not found or unauthorized'}), 403
        
        # Get payment for this gig
        payment = db.query(Payment).filter(Payment.gig_id == gig.id).order_by(Payment.created_at.desc()).first()
        
        if not payment:
            return jsonify({'status': 'no_payment', 'message': 'No payment found'}), 200
        
        # If already completed or failed, return cached status
        if payment.status in [TransactionStatus.COMPLETED, TransactionStatus.FAILED, TransactionStatus.CANCELLED]:
            return jsonify({
                'status': payment.status.value,
                'amount': payment.amount,
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None
            }), 200
        
        # Check status with PesaPal
        if payment.pesapal_order_tracking_id:
            try:
                pesapal = PesaPal()
                status_response = pesapal.get_transaction_status(payment.pesapal_order_tracking_id)
                
                payment_status = status_response.get('payment_status_description', '').lower()
                
                if payment_status == 'completed':
                    payment.status = TransactionStatus.COMPLETED
                    payment.completed_at = datetime.utcnow()
                    payment.pesapal_transaction_id = status_response.get('merchant_reference')
                    payment.payment_method = status_response.get('payment_method')
                    db.commit()
                    
                    return jsonify({
                        'status': 'completed',
                        'amount': payment.amount,
                        'completed_at': payment.completed_at.isoformat()
                    }), 200
                    
                elif payment_status == 'failed':
                    payment.status = TransactionStatus.FAILED
                    db.commit()
                    return jsonify({'status': 'failed'}), 200
                    
                elif payment_status == 'cancelled':
                    payment.status = TransactionStatus.CANCELLED
                    db.commit()
                    return jsonify({'status': 'cancelled'}), 200
                    
            except Exception as e:
                print(f"Error checking payment status: {e}")
        
        # Still pending
        return jsonify({'status': 'pending'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/jobs/<int:gig_id>/close', methods=['POST'])
@login_required
@role_required('institution')
def close_gig(gig_id):
    """Institution closes a gig (session-based auth)"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            return jsonify({'error': 'Gig not found or unauthorized'}), 403
        
        if gig.status == JobStatus.CLOSED:
            return jsonify({'error': 'Gig is already closed'}), 400
        
        gig.status = JobStatus.CLOSED
        gig.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({'message': 'Gig closed successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/jobs/<int:gig_id>', methods=['DELETE'])
@login_required
@role_required('institution')
def delete_gig_api(gig_id):
    """Institution deletes a gig (session-based auth)"""
    from flask import jsonify
    from app.models.payment import Payment
    from app.models.job import GigInterest
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            return jsonify({'error': 'Gig not found or unauthorized'}), 403
        
        # Only allow deletion of open or assigned gigs
        if gig.status not in [JobStatus.OPEN, JobStatus.ASSIGNED]:
            return jsonify({'error': 'Only open or assigned gigs can be deleted'}), 400
        
        # Get interested professionals and gig info BEFORE deleting anything
        job_interests = db.query(JobInterest).filter(JobInterest.job_id == gig_id).all()
        gig_interests = db.query(GigInterest).filter(GigInterest.job_id == gig_id).all()
        
        interested_professionals_user_ids = []
        for interest in job_interests:
            if interest.professional and interest.professional.user_id:
                interested_professionals_user_ids.append(interest.professional.user_id)
        for interest in gig_interests:
            if interest.professional and interest.professional.user_id:
                interested_professionals_user_ids.append(interest.professional.user_id)
        
        gig_title = gig.title
        
        # Delete related records in order
        # 1. Delete payments
        db.query(Payment).filter(Payment.gig_id == gig_id).delete(synchronize_session=False)
        
        # 2. Delete job interests (job_interests table)
        db.query(JobInterest).filter(JobInterest.job_id == gig_id).delete(synchronize_session=False)
        
        # 3. Delete gig interests (gig_interests table)
        db.query(GigInterest).filter(GigInterest.job_id == gig_id).delete(synchronize_session=False)
        
        # 4. Finally delete the gig
        db.delete(gig)
        db.commit()
        
        # Notify affected professionals
        from app import socketio
        for user_id in set(interested_professionals_user_ids):  # Use set to avoid duplicates
            socketio.emit('notification', {
                'message': f'The gig "{gig_title}" is no longer available.'
            }, room=f'user_{user_id}')
        
        return jsonify({'message': 'Gig deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        print(f"Delete error: {e}")  # Log the error
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/gigs/<int:gig_id>/delete', methods=['POST'])
@login_required
@role_required('institution')
def delete_gig(gig_id):
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        
        if not gig:
            flash('Gig not found or you do not have permission to delete it', 'error')
            return redirect(url_for('web.my_gigs'))
        
        if gig.status != JobStatus.OPEN:
            flash('Only open gigs can be deleted', 'error')
            return redirect(url_for('web.my_gigs'))
        
        db.delete(gig)
        db.commit()
        flash('Gig deleted successfully', 'success')
        return redirect(url_for('web.my_gigs'))
    finally:
        db.close()

@web_blueprint.route('/gigs/<int:gig_id>/interested')
@login_required
@role_required('institution')
def view_interested(gig_id):
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        gig = db.query(Job).options(joinedload(Job.institution)).filter(
            Job.id == gig_id, 
            Job.institution_id == institution.id
        ).first()
        
        if not gig:
            flash('Gig not found', 'error')
            return redirect(url_for('web.my_gigs'))
        
        interests = db.query(JobInterest).options(
            joinedload(JobInterest.professional)
        ).filter(JobInterest.job_id == gig_id).order_by(desc(JobInterest.created_at)).all()
        
        return render_template('interested_professionals.html', gig=gig, interests=interests)
    finally:
        db.close()

@web_blueprint.route('/jobs/<int:gig_id>/assign/<int:professional_id>', methods=['POST'])
@login_required
@role_required('institution')
def assign_gig_web(gig_id, professional_id):
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404

        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            return jsonify({'error': 'Gig not found or unauthorized'}), 404

        if gig.status != JobStatus.OPEN:
            return jsonify({'error': 'Gig is not open'}), 400

        professional = db.query(Professional).filter(Professional.id == professional_id).first()
        if not professional:
            return jsonify({'error': 'Professional not found'}), 404

        gig.assigned_professional_id = professional_id
        gig.status = JobStatus.ASSIGNED
        gig.updated_at = datetime.utcnow()

        db.commit()

        return jsonify({'message': 'Gig assigned successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/gigs/<int:gig_id>/express-interest', methods=['POST'])
@login_required
@role_required('professional')
def express_interest(gig_id):
    import logging
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    
    try:
        logger.info(f"Professional {session.get('user_id')} expressing interest in job {gig_id}")
        
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        
        if not professional:
            logger.warning(f"Professional profile not found for user {session.get('user_id')}")
            return jsonify({'error': 'Please complete your professional profile first'}), 400
        
        gig = db.query(Job).filter(Job.id == gig_id).first()
        
        if not gig:
            logger.warning(f"Job {gig_id} not found")
            return jsonify({'error': 'Job not found'}), 404
        
        if gig.status != JobStatus.OPEN:
            logger.warning(f"Job {gig_id} is not open (status: {gig.status})")
            return jsonify({'error': 'This job is no longer accepting interest'}), 400
        
        existing = db.query(JobInterest).filter(
            JobInterest.job_id == gig_id,
            JobInterest.professional_id == professional.id
        ).first()
        
        if existing:
            logger.info(f"Professional {professional.id} already expressed interest in job {gig_id}")
            return jsonify({'error': 'You have already expressed interest in this job'}), 400
        
        # Create interest
        interest = JobInterest(
            job_id=gig_id,
            professional_id=professional.id
        )
        db.add(interest)
        db.flush()  # Flush to get the interest.id without committing
        
        # Create notification for institution - NOW interest.id exists
        notification = Notification(
            user_id=gig.institution.user_id,
            title="New Interest in Your Job",
            message=f"{professional.full_name} has expressed interest in your job: {gig.title}",
            job_interest_id=interest.id,  # Now this has a value!
            role_context='institution'  # This notification is for institution role
        )
        db.add(notification)
        
        # COMMIT BEFORE EMITTING
        db.commit()
        db.refresh(interest)
        db.refresh(notification)
        
        logger.info(f"Interest {interest.id} created, notification {notification.id} saved")
        
        # Get professional documents
        from app.models.document import Document, DocumentType
        cv_doc = db.query(Document).filter(
            Document.professional_id == professional.id,
            Document.document_type == DocumentType.CV
        ).first()
        
        certificates = db.query(Document).filter(
            Document.professional_id == professional.id,
            Document.document_type == DocumentType.CERTIFICATE
        ).all()
        
        logger.info(f"CV Document found: {cv_doc is not None}")
        if cv_doc:
            logger.info(f"CV: {cv_doc.file_name}, Size: {cv_doc.file_size}")
        logger.info(f"Certificates found: {len(certificates)}")
        for cert in certificates:
            logger.info(f"Certificate: {cert.file_name}, Size: {cert.file_size}")
        
        # Send real-time notification via Socket.IO AFTER commit
        try:
            from app.sockets import send_interest_notification
            institution_id = gig.institution.id
            notification_data = {
                'notification_id': notification.id,
                'job_interest_id': interest.id,
                'professional_id': professional.id,
                'professional_name': professional.full_name,
                'job_id': gig.id,
                'job_title': gig.title,
                'institution_id': institution_id,
                'status': 'pending',
                'message': notification.message,
                'timestamp': notification.created_at.isoformat(),
                # Profile summary data
                'profile': {
                    'full_name': professional.full_name,
                    'phone_number': professional.phone_number,
                    'location': professional.location,
                    'profession_category': professional.profession_category,
                    'specialization': professional.specialization,
                    'skills': professional.skills,
                    'bio': professional.bio,
                    'hourly_rate': professional.hourly_rate,
                    'daily_rate': professional.daily_rate,
                    'registration_number': professional.registration_number,
                    'issuing_body': professional.issuing_body,
                    'experience': professional.experience,
                    'education': professional.education,
                    'certifications': professional.certifications,
                    'profile_picture': professional.profile_picture
                },
                # Document files
                'documents': {
                    'cv': {
                        'id': cv_doc.id,
                        'name': cv_doc.file_name,
                        'url': cv_doc.file_path,
                        'size': cv_doc.file_size
                    } if cv_doc else None,
                    'certificates': [
                        {
                            'id': cert.id,
                            'name': cert.file_name,
                            'url': cert.file_path,
                            'size': cert.file_size
                        } for cert in certificates
                    ]
                }
            }
            
            # Log the complete notification data being sent
            logger.info("=== NOTIFICATION DATA BEING SENT ===")
            logger.info(f"Profile data: {notification_data.get('profile', {})}")
            logger.info(f"Documents data: {notification_data.get('documents', {})}")
            logger.info(f"CV in notification: {notification_data['documents']['cv']}")
            logger.info(f"Certificates count in notification: {len(notification_data['documents']['certificates'])}")
            
            send_interest_notification(institution_id, notification_data)
            logger.info("Socket.IO notification sent successfully")
        except Exception as socket_error:
            logger.error(f"Socket.IO emission failed: {socket_error}", exc_info=True)
        
        return jsonify({
            'success': True,
            'message': 'Interest submitted successfully',
            'interest_id': interest.id
        }), 200
        
    except Exception as e:
        logger.error(f"Error in express_interest: {e}", exc_info=True)
        db.rollback()
        return jsonify({'error': 'An error occurred while submitting interest', 'details': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/gigs/my-assignments')
@login_required
@role_required('professional')
def my_assignments():
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    
    try:
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        
        if not professional:
            flash('Please complete your professional profile first', 'warning')
            return redirect(url_for('web.profile'))
        
        gigs = db.query(Job).options(
            joinedload(Job.institution)
        ).filter(Job.assigned_professional_id == professional.id).order_by(desc(Job.created_at)).all()
        
        return render_template('my_assignments.html', gigs=gigs)
    finally:
        db.close()

# ===== Profile Routes =====

@web_blueprint.route('/profile')
@login_required
def profile():
    from app.models.document import Document, DocumentType
    db = SessionLocal()
    
    user = db.query(User).filter(User.id == session['user_id']).first()
    
    profile = None
    uploaded_files = []
    
    if user.role == UserRole.PROFESSIONAL:
        profile = db.query(Professional).filter(Professional.user_id == user.id).first()
        # Create profile if it doesn't exist
        if not profile:
            profile = Professional(user_id=user.id)
            db.add(profile)
            db.commit()
        
        # Get uploaded documents
        documents = db.query(Document).filter(Document.professional_id == profile.id).all()
        for doc in documents:
            uploaded_files.append({
                'id': doc.id,
                'type': doc.document_type.value,
                'name': doc.file_name,
                'size': doc.file_size,
                'uploaded_at': doc.uploaded_at,
                'status': doc.status.value,
                'url': f'/api/professional/{profile.id}/download/{doc.id}'
            })
        
        # Ensure profile picture is set from Document table if available
        if not profile.profile_picture:
            profile_pic_doc = db.query(Document).filter(
                Document.professional_id == profile.id,
                Document.document_type == DocumentType.PROFILE_PICTURE
            ).first()
            if profile_pic_doc:
                profile.profile_picture = profile_pic_doc.file_path
                
    elif user.role == UserRole.INSTITUTION:
        profile = db.query(Institution).filter(Institution.user_id == user.id).first()
        # Create profile if it doesn't exist
        if not profile:
            profile = Institution(user_id=user.id)
            db.add(profile)
            db.commit()
    
    # Get ratings
    ratings = db.query(Rating).filter(Rating.rated_id == user.id).all()
    average_rating = db.query(func.avg(Rating.rating)).filter(Rating.rated_id == user.id).scalar() or 0
    
    # Get stats
    stats = {}
    if user.role == UserRole.PROFESSIONAL and profile:
        completed_gigs = db.query(Job).filter(
            Job.assigned_professional_id == profile.id,
            Job.status == JobStatus.COMPLETED
        ).count()
        
        total_earned = db.query(func.sum(Payment.amount)).filter(
            Payment.professional_id == profile.id,
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        stats = {
            'completed_gigs': completed_gigs,
            'total_earned': total_earned
        }
    elif user.role == UserRole.INSTITUTION and profile:
        total_gigs = db.query(Job).filter(Job.institution_id == profile.id).count()
        
        total_spent = db.query(func.sum(Payment.amount)).filter(
            Payment.institution_id == profile.id,
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        stats = {
            'total_gigs': total_gigs,
            'total_spent': total_spent
        }
    
    db.close()
    
    return render_template('profile.html', 
                         profile=profile, 
                         average_rating=average_rating,
                         total_ratings=len(ratings),
                         stats=stats,
                         uploaded_files=uploaded_files)

@web_blueprint.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    import os
    from werkzeug.utils import secure_filename
    
    db = SessionLocal()
    
    user = db.query(User).filter(User.id == session['user_id']).first()
    
    # Update username
    username = request.form.get('username')
    if username and username != user.username:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            flash('Username already taken. Please choose another.', 'error')
            db.close()
            return redirect(url_for('web.profile'))
        user.username = username
    
    if user.role == UserRole.PROFESSIONAL:
        profile = db.query(Professional).filter(Professional.user_id == user.id).first()
        if not profile:
            profile = Professional(user_id=user.id)
            db.add(profile)
        
        profile.name = request.form.get('name')
        profile.phone_number = request.form.get('phone_number')
        profile.skills = request.form.get('skills')
        profile.bio = request.form.get('bio')
        profile.profession_category = request.form.get('profession_category')
        profile.registration_number = request.form.get('registration_number')
        profile.issuing_body = request.form.get('issuing_body')
        profile.specialization = request.form.get('specialization')
        profile.education = request.form.get('education')
        profile.certifications = request.form.get('certifications')
        profile.experience = request.form.get('experience')
        profile.languages = request.form.get('languages')
        profile.hourly_rate = float(request.form.get('hourly_rate')) if request.form.get('hourly_rate') else None
        profile.daily_rate = float(request.form.get('daily_rate')) if request.form.get('daily_rate') else None
        profile.location = request.form.get('location')
        
        # Validate Health/Formal professions require registration
        if profile.profession_category in ['Health', 'Formal']:
            if not profile.registration_number or not profile.issuing_body:
                flash('Registration number and issuing body are required for Health and Formal professions', 'error')
                db.close()
                return redirect(url_for('web.profile'))
        
        # Handle file uploads
        upload_folder = os.path.join('app', 'static', 'uploads', 'professionals', str(user.id))
        os.makedirs(upload_folder, exist_ok=True)
        
        # CV upload
        if 'cv_file' in request.files:
            cv_file = request.files['cv_file']
            if cv_file and cv_file.filename:
                filename = secure_filename(cv_file.filename)
                cv_path = os.path.join(upload_folder, f'cv_{filename}')
                cv_file.save(cv_path)
                profile.cv_file = f'/static/uploads/professionals/{user.id}/cv_{filename}'
        
        # Certificate uploads (multiple)
        if 'certificate_files' in request.files:
            cert_files = request.files.getlist('certificate_files')
            cert_paths = []
            for cert_file in cert_files:
                if cert_file and cert_file.filename:
                    filename = secure_filename(cert_file.filename)
                    cert_path = os.path.join(upload_folder, f'cert_{filename}')
                    cert_file.save(cert_path)
                    cert_paths.append(f'/static/uploads/professionals/{user.id}/cert_{filename}')
            if cert_paths:
                profile.certificate_files = ','.join(cert_paths)
        
        # Profile picture upload
        if 'profile_picture' in request.files:
            pic_file = request.files['profile_picture']
            if pic_file and pic_file.filename:
                filename = secure_filename(pic_file.filename)
                pic_path = os.path.join(upload_folder, f'profile_{filename}')
                pic_file.save(pic_path)
                profile.profile_picture = f'/static/uploads/professionals/{user.id}/profile_{filename}'
        
    elif user.role == UserRole.INSTITUTION:
        profile = db.query(Institution).filter(Institution.user_id == user.id).first()
        if not profile:
            profile = Institution(user_id=user.id)
            db.add(profile)
        
        profile.name = request.form.get('name')
        profile.description = request.form.get('description')
        profile.contact_email = request.form.get('contact_email')
        profile.contact_phone = request.form.get('contact_phone')
        profile.location = request.form.get('location')
    
    db.commit()
    db.close()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('web.profile'))

# ===== Other Routes =====




@web_blueprint.route('/notifications')
@login_required
def notifications():
    """Display notifications filtered by active role"""
    from sqlalchemy.orm import joinedload
    from app.models.document import Document, DocumentType
    db = SessionLocal()
    try:
        active_role = session.get('active_role')
        if not active_role and 'user_id' in session:
            user = db.query(User).filter(User.id == session['user_id']).first()
            active_role = user.role.value if user else None
        
        # Filter notifications by active role
        user_notifications = db.query(Notification).options(
            joinedload(Notification.job_interest).joinedload(JobInterest.job),
            joinedload(Notification.job_interest).joinedload(JobInterest.professional)
        ).filter(
            Notification.user_id == session['user_id'],
            or_(
                Notification.role_context == active_role,
                Notification.role_context == None  # Include notifications for all roles
            )
        ).order_by(desc(Notification.created_at)).all()
        
        # Enrich notifications with professional profile and documents
        notifications_data = []
        for notif in user_notifications:
            notif_data = {
                'notification': notif,
                'profile': None,
                'documents': {'cv': None, 'certificates': []},
                'is_verified': False
            }
            
            # If this is a job interest notification, get professional data
            if notif.job_interest_id and notif.job_interest and notif.job_interest.professional:
                professional = notif.job_interest.professional
                notif_data['profile'] = professional

                requires_registration = (professional.profession_category in ['Health', 'Formal']) if professional.profession_category else False
                notif_data['is_verified'] = bool(requires_registration and professional.registration_number and professional.issuing_body)
                
                # Get CV
                cv_doc = db.query(Document).filter(
                    Document.professional_id == professional.id,
                    Document.document_type == DocumentType.CV
                ).first()
                notif_data['documents']['cv'] = cv_doc
                
                # Get certificates
                certificates = db.query(Document).filter(
                    Document.professional_id == professional.id,
                    Document.document_type == DocumentType.CERTIFICATE
                ).all()
                notif_data['documents']['certificates'] = certificates
            
            notifications_data.append(notif_data)
        
        return render_template('notifications.html', notifications_data=notifications_data)
    finally:
        db.close()

@web_blueprint.route('/payments')
@login_required
def payments_history():
    db = SessionLocal()

    from sqlalchemy.orm import joinedload

    try:
        user = db.query(User).filter(User.id == session['user_id']).first()

        active_role = session.get('active_role', user.role.value if user else None)

        payments = []
        payment_query = db.query(Payment).options(
            joinedload(Payment.gig),
            joinedload(Payment.institution),
            joinedload(Payment.professional).joinedload(Professional.user)
        )

        if user and active_role == 'professional':
            professional = db.query(Professional).filter(Professional.user_id == user.id).first()
            if professional:
                payments = payment_query.filter(
                    Payment.professional_id == professional.id
                ).order_by(desc(Payment.created_at)).all()
        elif user and active_role == 'institution':
            institution = db.query(Institution).filter(Institution.user_id == user.id).first()
            if institution:
                payments = payment_query.filter(
                    Payment.institution_id == institution.id
                ).order_by(desc(Payment.created_at)).all()

        stats = {
            'total_payments': len(payments),
            'completed': len([p for p in payments if p.status == TransactionStatus.COMPLETED]),
            'pending': len([p for p in payments if p.status == TransactionStatus.PENDING]),
            'total_amount': sum(p.amount for p in payments if p.status == TransactionStatus.COMPLETED)
        }

        return render_template('payments.html', payments=payments, stats=stats)
    finally:
        db.close()

@web_blueprint.route('/payments/<int:payment_id>')
@login_required
def payment_detail(payment_id):
    db = SessionLocal()
    try:
        from sqlalchemy.orm import joinedload

        payment = db.query(Payment).options(
            joinedload(Payment.gig),
            joinedload(Payment.institution),
            joinedload(Payment.professional).joinedload(Professional.user)
        ).filter(Payment.id == payment_id).first()
        if not payment:
            flash('Payment not found', 'error')
            return redirect(url_for('web.payments_history'))
        
        # Verify user has access
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        
        if not ((institution and payment.institution_id == institution.id) or 
                (professional and payment.professional_id == professional.id)):
            flash('Unauthorized access', 'error')
            return redirect(url_for('web.payments_history'))
        
        return render_template('payment_detail.html', payment=payment)
    finally:
        db.close()

@web_blueprint.route('/gigs/<int:gig_id>/pay', methods=['GET', 'POST'])
@login_required
@role_required('institution')
def initiate_payment_page(gig_id):
    """Web route for payment initiation page"""
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            flash('Institution profile not found', 'error')
            return redirect(url_for('web.profile'))
        
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            flash('Job not found or unauthorized', 'error')
            return redirect(url_for('web.my_gigs'))
        
        if gig.status != JobStatus.ACCEPTED:
            flash('Job must be assigned before payment', 'warning')
            return redirect(url_for('web.gig_detail', gig_id=gig_id))
        
        if request.method == 'GET':
            # Show payment confirmation page
            professional = db.query(Professional).filter(Professional.id == gig.assigned_professional_id).first()
            return render_template('payment_confirm.html', gig=gig, professional=professional)
        
        # POST - Initiate payment
        import uuid
        merchant_reference = f"QGIG-{uuid.uuid4().hex[:12].upper()}"
        
        payment = Payment(
            gig_id=gig.id,
            institution_id=institution.id,
            professional_id=gig.assigned_professional_id,
            amount=gig.pay_amount,
            pesapal_merchant_reference=merchant_reference,
            status=TransactionStatus.PENDING
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        flash('Payment initiated successfully. You can now proceed to pay.', 'success')
        return redirect(url_for('web.payment_detail', payment_id=payment.id))
            
    finally:
        db.close()

@web_blueprint.route('/payments/success')
@login_required
def payment_success():
    """Payment success callback page"""
    return render_template('payment_success.html')

@web_blueprint.route('/payments/cancel')
@login_required
def payment_cancel():
    """Payment cancellation page"""
    return render_template('payment_cancel.html')

@web_blueprint.route('/gigs/<int:gig_id>/complete', methods=['POST'])
@login_required
@role_required('professional')
def complete_job(gig_id):
    """Professional marks job as complete"""
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            flash('Professional profile not found', 'error')
            return redirect(url_for('web.profile'))
        
        gig = db.query(Job).filter(
            Job.id == gig_id,
            Job.assigned_professional_id == professional.id
        ).first()
        
        if not gig:
            flash('Job not found or not assigned to you', 'error')
            return redirect(url_for('web.my_assignments'))
        
        # Check if payment is completed
        payment = db.query(Payment).filter(
            Payment.gig_id == gig_id,
            Payment.status == TransactionStatus.COMPLETED
        ).first()
        
        if not payment:
            flash('Job cannot be marked complete until payment is received', 'warning')
            return redirect(url_for('web.my_assignments'))
        
        # Update job status
        gig.status = JobStatus.COMPLETED
        gig.updated_at = datetime.utcnow()
        
        # Create notification for institution
        institution_user = db.query(User).filter(User.id == gig.institution.user_id).first()
        notification = Notification(
            user_id=institution_user.id,
            title="Job Completed",
            message=f"The job '{gig.title}' has been marked as completed by {professional.full_name}.",
            role_context='institution'  # This notification is for institution role
        )
        db.add(notification)
        db.commit()
        
        flash('Job marked as complete! Please rate your experience.', 'success')
        return redirect(url_for('web.rate_job', gig_id=gig_id))
    finally:
        db.close()

@web_blueprint.route('/gigs/<int:gig_id>/rate', methods=['GET', 'POST'])
@login_required
def rate_job(gig_id):
    """Rate a completed job"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == session['user_id']).first()
        gig = db.query(Job).filter(Job.id == gig_id).first()
        
        if not gig:
            flash('Job not found', 'error')
            return redirect(url_for('web.home'))
        
        # Verify user is involved in this job
        professional = db.query(Professional).filter(Professional.user_id == user.id).first()
        institution = db.query(Institution).filter(Institution.user_id == user.id).first()
        
        is_professional = professional and gig.assigned_professional_id == professional.id
        is_institution = institution and gig.institution_id == institution.id
        
        if not (is_professional or is_institution):
            flash('You are not authorized to rate this job', 'error')
            return redirect(url_for('web.home'))
        
        # Check if already rated
        if is_professional:
            rated_user_id = gig.institution.user_id
            existing_rating = db.query(Rating).filter(
                Rating.job_id == gig_id,
                Rating.rater_id == user.id
            ).first()
        else:
            rated_user_id = gig.assigned_professional.user_id
            existing_rating = db.query(Rating).filter(
                Rating.job_id == gig_id,
                Rating.rater_id == user.id
            ).first()
        
        if existing_rating:
            flash('You have already rated this job', 'info')
            return redirect(url_for('web.my_assignments' if is_professional else 'web.my_gigs'))
        
        if request.method == 'POST':
            rating_value = int(request.form.get('rating', 0))
            comment = request.form.get('comment', '').strip()
            
            if rating_value < 1 or rating_value > 5:
                flash('Please provide a rating between 1 and 5 stars', 'error')
                return redirect(url_for('web.rate_job', gig_id=gig_id))
            
            # Create rating
            rating = Rating(
                job_id=gig_id,
                rater_id=user.id,
                rated_id=rated_user_id,
                rating=rating_value,
                comment=comment
            )
            db.add(rating)
            
            # Create notification for rated user
            rated_user = db.query(User).filter(User.id == rated_user_id).first()
            # Determine role context based on who is being rated
            rated_role = 'professional' if rated_user.id == gig.assigned_professional.user_id else 'institution'
            notification = Notification(
                user_id=rated_user_id,
                title="New Rating Received",
                message=f"You received a {rating_value}-star rating for the job '{gig.title}'.",
                role_context=rated_role
            )
            db.add(notification)
            db.commit()
            
            flash('Thank you for your rating!', 'success')
            return redirect(url_for('web.my_assignments' if is_professional else 'web.my_gigs'))
        
        # GET - Show rating form
        rated_user = db.query(User).filter(User.id == rated_user_id).first()
        return render_template('rate_job.html', gig=gig, rated_user=rated_user, is_professional=is_professional)
    finally:
        db.close()

@web_blueprint.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    """Admin dashboard with comprehensive analytics"""
    db = SessionLocal()
    try:
        from datetime import timedelta
        from sqlalchemy.orm import joinedload
        
        # Get comprehensive analytics
        total_users = db.query(User).count()
        total_professionals = db.query(Professional).count()
        total_institutions = db.query(Institution).count()
        total_jobs = db.query(Job).count()
        open_jobs = db.query(Job).filter(Job.status == JobStatus.OPEN).count()
        assigned_jobs = db.query(Job).filter(Job.status == JobStatus.ASSIGNED).count()
        completed_jobs = db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        
        total_payments = db.query(Payment).count()
        completed_payments = db.query(Payment).filter(Payment.status == TransactionStatus.COMPLETED).count()
        pending_payments = db.query(Payment).filter(Payment.status == TransactionStatus.PENDING).count()
        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        pending_documents = db.query(Document).filter(Document.status == DocumentStatus.PENDING).count()
        approved_documents = db.query(Document).filter(Document.status == DocumentStatus.APPROVED).count()
        rejected_documents = db.query(Document).filter(Document.status == DocumentStatus.REJECTED).count()
        
        # Top institutions
        top_institutions = db.query(
            Institution.id,
            Institution.institution_name,
            func.count(Job.id).label('gig_count')
        ).join(Job).group_by(Institution.id, Institution.institution_name).order_by(
            func.count(Job.id).desc()
        ).limit(5).all()
        
        # Top professionals
        top_professionals = db.query(
            Professional.id,
            Professional.full_name,
            func.count(Job.id).label('hire_count')
        ).join(Job, Job.assigned_professional_id == Professional.id).filter(
            Job.status.in_([JobStatus.ASSIGNED, JobStatus.COMPLETED])
        ).group_by(Professional.id, Professional.full_name).order_by(
            func.count(Job.id).desc()
        ).limit(5).all()
        
        # Daily revenue (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_revenue = db.query(
            func.date(Payment.completed_at).label('date'),
            func.sum(Payment.amount).label('revenue')
        ).filter(
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= thirty_days_ago
        ).group_by(func.date(Payment.completed_at)).order_by(func.date(Payment.completed_at)).all()
        
        # Pending payments amount
        pending_payment_amount = db.query(func.sum(Payment.amount)).filter(
            Payment.status == TransactionStatus.PENDING
        ).scalar() or 0
        
        analytics = {
            'users': {
                'total': total_users,
                'professionals': total_professionals,
                'institutions': total_institutions
            },
            'gigs': {
                'total': total_jobs,
                'open': open_jobs,
                'assigned': assigned_jobs,
                'completed': completed_jobs
            },
            'payments': {
                'total': total_payments,
                'completed': completed_payments,
                'pending': pending_payments,
                'total_revenue': total_revenue,
                'pending_amount': pending_payment_amount
            },
            'documents': {
                'pending': pending_documents,
                'approved': approved_documents,
                'rejected': rejected_documents
            },
            'top_institutions': [{
                'id': inst.id,
                'name': inst.institution_name,
                'gig_count': inst.gig_count
            } for inst in top_institutions],
            'top_professionals': [{
                'id': prof.id,
                'name': prof.full_name,
                'hire_count': prof.hire_count
            } for prof in top_professionals],
            'daily_revenue': [{
                'date': str(dr.date),
                'revenue': float(dr.revenue)
            } for dr in daily_revenue]
        }

        # Tab data for server-rendered admin dashboard (avoid JWT-only API calls)
        users = db.query(User).order_by(desc(User.created_at)).limit(200).all()
        documents = db.query(Document).options(joinedload(Document.user)).order_by(desc(Document.uploaded_at)).limit(200).all()
        latest_payment_per_gig = db.query(
            Payment.gig_id.label('gig_id'),
            func.max(Payment.created_at).label('max_created_at')
        ).group_by(Payment.gig_id).subquery()

        payments = db.query(Payment).options(
            joinedload(Payment.gig),
            joinedload(Payment.institution),
            joinedload(Payment.professional)
        ).join(
            latest_payment_per_gig,
            (Payment.gig_id == latest_payment_per_gig.c.gig_id) &
            (Payment.created_at == latest_payment_per_gig.c.max_created_at)
        ).order_by(desc(Payment.created_at)).limit(200).all()

        return render_template('admin_dashboard_complete.html', analytics=analytics, users=users, documents=documents, payments=payments)
    finally:
        db.close()

@web_blueprint.route('/admin/documents')
@login_required
@role_required('admin')
def admin_documents():
    """Admin document verification page"""
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(
            Document.status == DocumentStatus.PENDING
        ).order_by(desc(Document.uploaded_at)).all()
        
        return render_template('admin_documents.html', documents=documents)
    finally:
        db.close()

@web_blueprint.route('/admin/documents/<int:document_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_document(document_id):
    """Approve a document"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('web.admin_documents'))
        
        document.status = DocumentStatus.APPROVED
        document.updated_at = datetime.utcnow()
        document.is_verified = 1
        document.reviewed_at = datetime.utcnow()
        document.reviewed_by = session.get('user_id')
        
        # Notify user
        notification = Notification(
            user_id=document.user_id,
            title="Document Approved",
            message=f"Your {document.document_type.value} has been approved.",
            role_context='professional'  # Document approvals are for professionals
        )
        db.add(notification)
        db.commit()
        
        flash('Document approved successfully', 'success')
        return redirect(url_for('web.admin_documents'))
    finally:
        db.close()

@web_blueprint.route('/admin/documents/<int:document_id>/reject', methods=['POST'])
@login_required
@role_required('admin')
def reject_document(document_id):
    """Reject a document"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('web.admin_documents'))
        
        reason = request.form.get('reason', 'Document did not meet requirements')
        
        document.status = DocumentStatus.REJECTED
        document.updated_at = datetime.utcnow()
        document.is_verified = 0
        document.reviewed_at = datetime.utcnow()
        document.reviewed_by = session.get('user_id')
        
        # Notify user
        notification = Notification(
            user_id=document.user_id,
            title="Document Rejected",
            message=f"Your {document.document_type.value} was rejected. Reason: {reason}",
            role_context='professional'  # Document rejections are for professionals
        )
        db.add(notification)
        db.commit()
        
        flash('Document rejected', 'success')
        return redirect(url_for('web.admin_documents'))
    finally:
        db.close()

@web_blueprint.route('/settings')
@login_required
def settings():
    """User settings page with account management options"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == session['user_id']).first()
        
        # Get role-specific profile
        profile = None
        if user.role == UserRole.PROFESSIONAL:
            profile = db.query(Professional).filter(Professional.user_id == user.id).first()
        elif user.role == UserRole.INSTITUTION:
            profile = db.query(Institution).filter(Institution.user_id == user.id).first()
        
        return render_template('settings.html', user=user, profile=profile)
    finally:
        db.close()

@web_blueprint.route('/settings/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    db = SessionLocal()
    try:
        data = request.get_json() if request.is_json else request.form
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Get user and verify current password
        user = db.query(User).filter(User.id == session['user_id']).first()
        
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Hash and update new password
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.password = new_hash
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/settings/update-email', methods=['POST'])
@login_required
def update_email():
    """Update user email address"""
    db = SessionLocal()
    try:
        data = request.get_json() if request.is_json else request.form
        new_email = data.get('new_email')
        password = data.get('password')
        
        if not all([new_email, password]):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, new_email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if email already exists
        existing = db.query(User).filter(User.email == new_email).first()
        if existing:
            return jsonify({'error': 'Email already in use'}), 409
        
        # Verify password
        user = db.query(User).filter(User.id == session['user_id']).first()
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({'error': 'Password is incorrect'}), 401
        
        # Update email
        user.email = new_email
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Email updated successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/settings/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account permanently"""
    db = SessionLocal()
    try:
        data = request.get_json() if request.is_json else request.form
        password = data.get('password')
        confirmation = data.get('confirmation')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if confirmation != 'DELETE':
            return jsonify({'error': 'Please type DELETE to confirm'}), 400
        
        # Verify password
        user = db.query(User).filter(User.id == session['user_id']).first()
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({'error': 'Password is incorrect'}), 401
        
        # Delete related data based on role
        if user.role == UserRole.PROFESSIONAL:
            # Delete professional profile and related data
            professional = db.query(Professional).filter(Professional.user_id == user.id).first()
            if professional:
                # Delete job interests
                db.query(JobInterest).filter(JobInterest.professional_id == professional.id).delete()
                # Delete professional profile
                db.delete(professional)
        
        elif user.role == UserRole.INSTITUTION:
            # Delete institution profile and related data
            institution = db.query(Institution).filter(Institution.user_id == user.id).first()
            if institution:
                # Delete jobs posted by institution
                jobs = db.query(Job).filter(Job.institution_id == institution.id).all()
                for job in jobs:
                    # Delete interests for each job
                    db.query(JobInterest).filter(JobInterest.job_id == job.id).delete()
                    db.delete(job)
                # Delete institution profile
                db.delete(institution)
        
        # Delete notifications
        db.query(Notification).filter(Notification.user_id == user.id).delete()
        
        # Delete messages (sent and received)
        db.query(Message).filter(
            (Message.sender_id == user.id) | (Message.receiver_id == user.id)
        ).delete()
        
        # Delete documents
        db.query(Document).filter(Document.user_id == user.id).delete()
        
        # Finally delete user
        db.delete(user)
        db.commit()
        
        # Logout user
        session.clear()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully', 'redirect': url_for('web.home')})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/settings/notification-preferences', methods=['POST'])
@login_required
def update_notification_preferences():
    """Update notification preferences"""
    db = SessionLocal()
    try:
        data = request.get_json() if request.is_json else request.form
        
        user = db.query(User).filter(User.id == session['user_id']).first()
        
        # Store preferences in user metadata (you may want to add a preferences column)
        # For now, return success
        
        return jsonify({'success': True, 'message': 'Notification preferences updated'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# ===== Interest-Based Workflow Routes =====

@web_blueprint.route('/professional/interested')
@login_required
@role_required('professional')
def professional_interested_page():
    """Render professional interested page"""
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            flash('Professional profile not found', 'error')
            return redirect(url_for('web.profile'))

        return render_template('professional_interested.html', professional_id=professional.id)
    finally:
        db.close()

# POST /jobs/{job_id}/interest - Professional shows interest in a job
@web_blueprint.route('/jobs/<int:job_id>/interest', methods=['POST'])
@login_required
@role_required('professional')
def show_job_interest(job_id):
    """Professional expresses interest in a job"""
    from flask import jsonify
    import logging
    logger = logging.getLogger(__name__)
    
    db = SessionLocal()
    
    try:
        logger.info(f"Professional {session.get('user_id')} showing interest in job {job_id}")
        
        # Get professional
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            logger.error(f"Professional profile not found for user {session.get('user_id')}")
            return jsonify({'error': 'Professional profile not found'}), 404
        
        # Get job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return jsonify({'error': 'Job not found'}), 404
        
        # Check if job is OPEN
        if job.status != JobStatus.OPEN:
            logger.warning(f"Job {job_id} is not open (status: {job.status})")
            return jsonify({'error': 'Job is not open for interest'}), 400
        
        # Check if already interested
        existing = db.query(JobInterest).filter(
            JobInterest.job_id == job_id,
            JobInterest.professional_id == professional.id
        ).first()
        
        if existing:
            logger.warning(f"Professional {professional.id} already interested in job {job_id}")
            return jsonify({'error': 'You have already shown interest in this job'}), 400
        
        # Create interest
        interest = JobInterest(
            job_id=job_id,
            professional_id=professional.id,
            status=InterestStatus.PENDING
        )
        db.add(interest)
        db.flush()
        
        # Create notification for institution with professional name and timestamp
        institution_user = db.query(User).filter(User.id == job.institution.user_id).first()
        if not institution_user:
            logger.error(f"Institution user not found for job {job_id}")
            db.rollback()
            return jsonify({'error': 'Institution not found'}), 404
        
        # Get username or fallback to full name
        prof_username = professional.user.username if professional.user.username else professional.full_name
        notification = Notification(
            user_id=institution_user.id,
            title=f"New Interest in Your Gig",
            message=f"{prof_username} has shown interest in your gig: {job.title}. Posted at {datetime.utcnow().strftime('%b %d, %Y at %I:%M %p')}",
            job_interest_id=interest.id,
            role_context='institution'  # This notification is for institution role
        )
        db.add(notification)
        
        # COMMIT BEFORE EMITTING
        db.commit()
        db.refresh(notification)
        db.refresh(interest)
        
        logger.info(f"Interest {interest.id} created, notification {notification.id} saved")
        
        # Send real-time notification via Socket.IO AFTER commit
        try:
            from app.sockets import send_interest_notification
            institution_id = job.institution.id
            
            notification_data = {
                'notification_id': notification.id,
                'job_interest_id': interest.id,
                'professional_id': professional.id,
                'professional_name': professional.full_name,
                'job_id': job.id,
                'job_title': job.title,
                'institution_id': institution_id,
                'status': 'pending',
                'message': notification.message,
                'timestamp': notification.created_at.isoformat()
            }
            
            logger.info(f"Emitting notification to institution {institution_id}: {notification_data}")
            send_interest_notification(institution_id, notification_data)
            logger.info(f"Socket.IO notification sent successfully")
        except Exception as socket_error:
            # Log but don't fail the request if Socket.IO fails
            logger.error(f"Socket.IO emission failed: {socket_error}", exc_info=True)
        
        # ALWAYS return success response
        return jsonify({
            'success': True,
            'message': 'Interest submitted successfully',
            'interest_id': interest.id
        }), 200
        
    except Exception as e:
        logger.error(f"Error in show_job_interest: {e}", exc_info=True)
        db.rollback()
        return jsonify({
            'error': 'An error occurred while submitting interest',
            'details': str(e)
        }), 500
    finally:
        db.close()

# POST /interests/{interest_id}/accept - Institution accepts an interest
@web_blueprint.route('/interests/<int:interest_id>/accept', methods=['POST'])
@login_required
@role_required('institution')
def accept_interest(interest_id):
    """Institution accepts a professional interest"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        # Get institution
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        # Get interest
        interest = db.query(JobInterest).filter(JobInterest.id == interest_id).first()
        if not interest:
            return jsonify({'error': 'Interest not found'}), 404
        
        # Verify institution owns the job
        job = interest.job
        if job.institution_id != institution.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if interest is pending
        if interest.status != InterestStatus.PENDING:
            return jsonify({'error': 'Interest has already been processed'}), 400
        
        # Accept the interest
        interest.status = InterestStatus.ACCEPTED
        interest.updated_at = datetime.utcnow()
        
        # Assign professional to job
        job.assigned_professional_id = interest.professional_id
        job.status = JobStatus.ACCEPTED
        
        # Decline all other pending interests for this job
        other_interests = db.query(JobInterest).filter(
            JobInterest.job_id == job.id,
            JobInterest.id != interest_id,
            JobInterest.status == InterestStatus.PENDING
        ).all()
        
        for other_interest in other_interests:
            other_interest.status = InterestStatus.DECLINED
            other_interest.updated_at = datetime.utcnow()
            
            # Notify declined professionals
            declined_user = db.query(User).filter(
                User.id == other_interest.professional.user_id
            ).first()
            declined_notification = Notification(
                user_id=declined_user.id,
                title="Interest Declined",
                message=f"Your interest in the gig '{job.title}' has been DECLINED.",
                role_context='professional',  # This notification is for professional role
                job_interest_id=other_interest.id
            )
            db.add(declined_notification)
            db.flush()
            
            # Send real-time notification to declined professional
            from app.sockets import send_rejection_notification
            send_rejection_notification(declined_user.id, {
                'notification_id': declined_notification.id,
                'institution_name': job.institution.institution_name,
                'job_title': job.title,
                'job_id': job.id,
                'decision': 'Rejected',
                'timestamp': declined_notification.created_at.strftime('%b %d, %Y at %I:%M %p'),
                'message': declined_notification.message
            })
        
        # Create automatic welcome message from institution to professional
        from app.models.message import Message, MessageStatus
        institution_user = db.query(User).filter(User.id == institution.user_id).first()
        accepted_user = db.query(User).filter(
            User.id == interest.professional.user_id
        ).first()
        
        welcome_message = Message(
            sender_id=institution_user.id,
            receiver_id=accepted_user.id,
            job_id=job.id,
            job_interest_id=interest.id,
            subject=f"Congratulations! Your interest in '{job.title}' has been accepted",
            content=f"Hello! We're pleased to inform you that your interest in the gig '{job.title}' has been accepted. "
                    f"Please feel free to reach out if you have any questions about the gig details, schedule, or requirements. "
                    f"We look forward to working with you!",
            status=MessageStatus.SENT
        )
        db.add(welcome_message)
        db.flush()
        
        # Notify accepted professional with chat link
        accepted_notification = Notification(
            user_id=accepted_user.id,
            title="Interest Accepted!",
            message=f"Your interest in the gig '{job.title}' has been ACCEPTED. A message from the institution is waiting for you.",
            role_context='professional',  # This notification is for professional role
            job_interest_id=interest.id
        )
        db.add(accepted_notification)
        
        db.commit()
        db.refresh(accepted_notification)
        db.refresh(welcome_message)
        
        # Send real-time notification to accepted professional
        from app.sockets import send_acceptance_notification, send_message_notification
        send_acceptance_notification(accepted_user.id, {
            'notification_id': accepted_notification.id,
            'institution_name': job.institution.institution_name,
            'job_title': job.title,
            'job_id': job.id,
            'decision': 'Accepted',
            'timestamp': accepted_notification.created_at.strftime('%b %d, %Y at %I:%M %p'),
            'message': accepted_notification.message,
            'chat_url': f'/messages/conversation/{institution_user.id}'
        })
        
        # Send real-time message notification
        send_message_notification(accepted_user.id, {
            'message_id': welcome_message.id,
            'sender_id': institution_user.id,
            'content': welcome_message.content,
            'created_at': welcome_message.created_at.isoformat(),
            'job_id': job.id
        })
        
        return jsonify({
            'success': True,
            'message': 'Interest accepted successfully',
            'chat_url': f'/messages/conversation/{accepted_user.id}'
        })
    finally:
        db.close()

# POST /interests/{interest_id}/decline - Institution declines an interest
@web_blueprint.route('/interests/<int:interest_id>/decline', methods=['POST'])
@login_required
@role_required('institution')
def decline_interest(interest_id):
    """Institution declines a professional interest"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        # Get institution
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        # Get interest
        interest = db.query(JobInterest).filter(JobInterest.id == interest_id).first()
        if not interest:
            return jsonify({'error': 'Interest not found'}), 404
        
        # Verify institution owns the job
        job = interest.job
        if job.institution_id != institution.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if interest is pending
        if interest.status != InterestStatus.PENDING:
            return jsonify({'error': 'Interest has already been processed'}), 400
        
        # Decline the interest
        interest.status = InterestStatus.DECLINED
        interest.updated_at = datetime.utcnow()
        
        # Notify professional
        professional_user = db.query(User).filter(
            User.id == interest.professional.user_id
        ).first()
        notification = Notification(
            user_id=professional_user.id,
            title="Interest Declined",
            message=f"Your interest in the gig '{job.title}' has been DECLINED.",
            job_interest_id=interest.id,
            role_context='professional'  # This notification is for professional role
        )
        db.add(notification)
        
        db.commit()
        db.refresh(notification)
        
        # Send real-time notification to professional
        from app.sockets import send_rejection_notification
        send_rejection_notification(professional_user.id, {
            'notification_id': notification.id,
            'institution_name': job.institution.institution_name,
            'job_title': job.title,
            'job_id': job.id,
            'decision': 'Rejected',
            'timestamp': notification.created_at.strftime('%b %d, %Y at %I:%M %p'),
            'message': notification.message
        })
        
        return jsonify({
            'success': True,
            'message': 'Interest declined successfully'
        })
    finally:
        db.close()

# POST /jobs/{job_id}/cancel-interest - Professional cancels their interest
@web_blueprint.route('/jobs/<int:job_id>/cancel-interest', methods=['POST'])
@login_required
@role_required('professional')
def cancel_interest(job_id):
    """Professional cancels their interest in a job (session-based auth)"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            return jsonify({'error': 'Professional profile not found'}), 404
        
        interest = db.query(JobInterest).filter(
            JobInterest.job_id == job_id,
            JobInterest.professional_id == professional.id
        ).first()
        
        if not interest:
            return jsonify({'error': 'Interest not found'}), 404
        
        job = interest.job
        institution_user_id = job.institution.user_id
        
        # If job was assigned to this professional, reopen it
        if job.status == JobStatus.ASSIGNED and job.assigned_professional_id == professional.id:
            job.status = JobStatus.OPEN
            job.assigned_professional_id = None
        
        # Create notification for institution about cancellation
        # Get username or fallback to full name
        prof_username = professional.user.username if professional.user.username else professional.full_name
        notification = Notification(
            user_id=institution_user_id,
            title="Interest Withdrawn",
            message=f"{prof_username} has withdrawn their interest in your job: {job.title}",
            job_interest_id=None,
            role_context='institution'  # This notification is for institution role
        )
        db.add(notification)
        
        db.delete(interest)
        db.commit()
        
        # Notify institution via Socket.IO
        from app import socketio
        socketio.emit('notification', {
            'message': f'{prof_username} has withdrawn their interest in {job.title}'
        }, room=f'user_{institution_user_id}')
        
        return jsonify({'message': 'Interest canceled successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# GET /notifications - Get user notifications
@web_blueprint.route('/api/notifications')
@login_required
def get_notifications():
    """Get notifications for current user"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        from sqlalchemy.orm import joinedload

        notifications = db.query(Notification).options(
            joinedload(Notification.job_interest)
        ).filter(
            Notification.user_id == session['user_id']
        ).order_by(desc(Notification.created_at)).limit(50).all()
        
        result = []
        for notif in notifications:
            notif_data = {
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat()
            }
            
            # Add job interest details if available
            if notif.job_interest_id:
                notif_data['job_interest_id'] = notif.job_interest_id
            
            result.append(notif_data)
        
        return jsonify(result)
    finally:
        db.close()

# Mark all notifications as read
@web_blueprint.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all unread notifications as read for the current active role"""
    from flask import jsonify
    db = SessionLocal()
    try:
        active_role = session.get('active_role')
        if not active_role and 'user_id' in session:
            user = db.query(User).filter(User.id == session['user_id']).first()
            active_role = user.role.value if user else None
        
        # Update all unread notifications for this user and role
        updated = db.query(Notification).filter(
            Notification.user_id == session['user_id'],
            Notification.is_read == False,
            or_(
                Notification.role_context == active_role,
                Notification.role_context == None
            )
        ).update({Notification.is_read: True}, synchronize_session=False)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'Marked {updated} notification(s) as read',
            'count': updated
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# Mark single notification as read
@web_blueprint.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a single notification as read"""
    from flask import jsonify
    db = SessionLocal()
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == session['user_id']
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        notification.is_read = True
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# Delete single notification
@web_blueprint.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete a single notification"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == session['user_id']
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        db.delete(notification)
        db.commit()
        
        return jsonify({'success': True, 'message': 'Notification deleted'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# Delete selected notifications
@web_blueprint.route('/api/notifications/delete-selected', methods=['POST'])
@login_required
def delete_selected_notifications():
    """Delete multiple selected notifications"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        data = request.json
        notification_ids = data.get('notification_ids', [])
        
        if not notification_ids:
            return jsonify({'error': 'No notification IDs provided'}), 400
        
        deleted_count = db.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == session['user_id']
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'{deleted_count} notification(s) deleted'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# Delete all notifications
@web_blueprint.route('/api/notifications/delete-all', methods=['DELETE'])
@login_required
def delete_all_notifications():
    """Delete all notifications for current user"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        deleted_count = db.query(Notification).filter(
            Notification.user_id == session['user_id']
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'All {deleted_count} notification(s) deleted'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/professional/<int:professional_id>/interested-jobs')
@login_required
@role_required('professional')
def professional_interested_jobs(professional_id):
    """Get jobs the professional marked as interested"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        professional = db.query(Professional).filter(Professional.id == professional_id).first()
        if not professional or professional.user_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        interests = db.query(JobInterest).filter(
            JobInterest.professional_id == professional_id
        ).all()
        
        result = []
        for interest in interests:
            job = db.query(Job).filter(Job.id == interest.job_id).first()
            if job:
                result.append({
                    'id': job.id,
                    'title': job.title,
                    'description': job.description,
                    'pay_amount': job.pay_amount,
                    'location': job.location,
                    'status': job.status.value,
                    'interest_status': interest.status.value.capitalize(),
                    'institution_name': job.institution.institution_name,
                    'institution_id': job.institution.id,
                    'created_at': interest.created_at.isoformat()
                })
        
        return jsonify(result)
    finally:
        db.close()

@web_blueprint.route('/professional/earnings')
@login_required
@role_required('professional')
def professional_earnings():
    """Professional Earnings and Payment History Page"""
    from sqlalchemy.orm import joinedload
    from datetime import datetime, timedelta
    db = SessionLocal()
    try:
        professional = db.query(Professional).filter(Professional.user_id == session['user_id']).first()
        if not professional:
            flash('Professional profile not found', 'error')
            return redirect(url_for('web.profile'))
        
        # Get all payments
        payments = db.query(Payment).options(
            joinedload(Payment.gig),
            joinedload(Payment.institution)
        ).filter(
            Payment.professional_id == professional.id
        ).order_by(desc(Payment.created_at)).all()
        
        # Calculate totals
        total_earnings = db.query(func.sum(Payment.amount)).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        pending_amount = db.query(func.sum(Payment.amount)).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.PENDING
        ).scalar() or 0
        
        completed_count = db.query(Payment).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.COMPLETED
        ).count()
        
        pending_count = db.query(Payment).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.PENDING
        ).count()
        
        # Monthly earnings (this month)
        now = datetime.utcnow()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_earnings = db.query(func.sum(Payment.amount)).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= first_day_of_month
        ).scalar() or 0
        
        monthly_count = db.query(Payment).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= first_day_of_month
        ).count()
        
        # Monthly trend (last 6 months)
        six_months_ago = now - timedelta(days=180)
        monthly_data = db.query(
            func.strftime('%Y-%m', Payment.completed_at).label('month'),
            func.sum(Payment.amount).label('amount')
        ).filter(
            Payment.professional_id == professional.id,
            Payment.status == TransactionStatus.COMPLETED,
            Payment.completed_at >= six_months_ago
        ).group_by('month').order_by('month').all()
        
        monthly_trend = [{'month': m.month, 'amount': float(m.amount)} for m in monthly_data]
        
        return render_template('professional_earnings.html',
                             payments=payments,
                             total_earnings=total_earnings,
                             pending_amount=pending_amount,
                             completed_count=completed_count,
                             pending_count=pending_count,
                             monthly_earnings=monthly_earnings,
                             monthly_count=monthly_count,
                             monthly_trend=monthly_trend)
    finally:
        db.close()

@web_blueprint.route('/professional/<int:professional_id>/interested-institutions')
@login_required
@role_required('professional')
def professional_interested_institutions(professional_id):
    """Get institutions that marked this professional as interested"""
    from flask import jsonify
    db = SessionLocal()
    
    try:
        professional = db.query(Professional).filter(Professional.id == professional_id).first()
        if not professional or professional.user_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get jobs assigned to this professional
        assigned_jobs = db.query(Job).filter(
            Job.assigned_professional_id == professional_id
        ).all()
        
        result = []
        for job in assigned_jobs:
            result.append({
                'job_id': job.id,
                'job_title': job.title,
                'institution_name': job.institution.institution_name,
                'institution_id': job.institution.id,
                'pay_amount': job.pay_amount,
                'status': job.status.value
            })
        
        return jsonify(result)
    finally:
        db.close()

@web_blueprint.route('/edit-profile')
@login_required
def edit_profile():
    return redirect(url_for('web.profile'))

@web_blueprint.route('/gigs/<int:gig_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('institution')
def edit_gig(gig_id):
    db = SessionLocal()
    
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            flash('Institution profile not found', 'error')
            return redirect(url_for('web.my_gigs'))
        
        gig = db.query(Job).filter(Job.id == gig_id, Job.institution_id == institution.id).first()
        if not gig:
            flash('Gig not found or unauthorized', 'error')
            return redirect(url_for('web.my_gigs'))
        
        # Only allow editing of open or assigned gigs
        if gig.status not in [JobStatus.OPEN, JobStatus.ASSIGNED]:
            flash('Only open or assigned gigs can be edited', 'error')
            return redirect(url_for('web.my_gigs'))
        
        if request.method == 'POST':
            # Update gig fields
            gig.title = request.form.get('title')
            gig.description = request.form.get('description')
            gig.location = request.form.get('location')
            gig.job_type = request.form.get('job_type')
            gig.sector = request.form.get('sector')
            gig.pay_amount = float(request.form.get('pay_amount'))
            gig.duration_hours = float(request.form.get('duration_hours')) if request.form.get('duration_hours') else None
            gig.is_urgent = bool(request.form.get('is_urgent'))
            
            # Handle expiry date for urgent gigs
            if gig.is_urgent and request.form.get('expiry_date'):
                gig.expiry_date = datetime.fromisoformat(request.form.get('expiry_date'))
            else:
                gig.expiry_date = None
            
            db.commit()
            flash('Gig updated successfully!', 'success')
            return redirect(url_for('web.my_gigs'))
        
        return render_template('edit_gig.html', gig=gig)
    finally:
        db.close()

# Static pages
@web_blueprint.route('/about')
def about():
    return render_template('static_page.html', title='About Us', content='About QGig content...')

@web_blueprint.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

@web_blueprint.route('/contact')
def contact():
    return render_template('contact.html')

@web_blueprint.route('/faq')
def faq():
    return render_template('faq.html')

@web_blueprint.route('/terms')
def terms():
    return render_template('terms.html')

@web_blueprint.route('/privacy')
def privacy():
    return render_template('privacy.html')

@web_blueprint.route('/help')
def help():
    return render_template('help_full.html')

@web_blueprint.route('/notifications/<int:notification_id>/respond', methods=['POST'])
@login_required
@role_required('institution')
def respond_to_notification(notification_id):
    """Institution responds to interest notification - wrapper for gig-interests endpoint"""
    data = request.get_json()
    action = data.get('action')

    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Invalid action. Must be "accept" or "reject"'}), 400

    db = SessionLocal()
    try:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification or not notification.job_interest_id:
            return jsonify({'error': 'Notification not found or not related to a job interest'}), 404

        # Redirect to the main gig-interests respond endpoint
        interest_id = notification.job_interest_id
        db.close()
        
        # Call the main respond endpoint logic
        return respond_to_gig_interest(interest_id, action)
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if db:
            db.close()

# Main endpoint per spec: POST /gig-interests/<interest_id>/respond
@web_blueprint.route('/gig-interests/<int:interest_id>/respond', methods=['POST'])
@login_required
@role_required('institution')
def gig_interest_respond(interest_id):
    """Institution accepts or rejects a professional interest"""
    data = request.get_json()
    action = data.get('action')
    
    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Invalid action. Must be "accept" or "reject"'}), 400
    
    return respond_to_gig_interest(interest_id, action)

def respond_to_gig_interest(interest_id, action):
    """Core logic for accepting/rejecting interest - called by both endpoints"""
    db = SessionLocal()
    try:
        # 1. Validate user is logged in (already done by decorator)
        # 2. Confirm user role is Institution (already done by decorator)
        
        # 3. Fetch gig_interest by ID - MUST query before using
        interest = db.query(JobInterest).filter(JobInterest.id == interest_id).first()
        if not interest:
            return jsonify({'error': 'Interest not found'}), 404
        
        # 4a. Ensure interest belongs to Institution
        job = interest.job
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution profile not found'}), 404
        
        if job.institution_id != institution.id:
            return jsonify({'error': 'Unauthorized - this interest does not belong to your institution'}), 403
        
        # 4b. Ensure status is pending
        if interest.status != InterestStatus.PENDING:
            return jsonify({
                'error': 'Interest has already been processed',
                'current_status': interest.status.value
            }), 409
        
        # Get professional info before any changes
        professional = interest.professional
        professional_user_id = professional.user_id
        gig_title = job.title
        institution_name = institution.institution_name
        
        # 5. Update status based on action
        if action == 'accept':
            interest.status = InterestStatus.ACCEPTED
            job.status = JobStatus.ASSIGNED
            job.assigned_professional_id = interest.professional_id
            decision = 'accepted'
            
            # Reject all other pending interests for this job
            other_interests = db.query(JobInterest).filter(
                JobInterest.job_id == job.id,
                JobInterest.id != interest_id,
                JobInterest.status == InterestStatus.PENDING
            ).all()
            
            for other in other_interests:
                other.status = InterestStatus.DECLINED
                other.updated_at = datetime.utcnow()
                
                # Create notification for rejected professional
                rejected_notif = Notification(
                    user_id=other.professional.user_id,
                    title="Interest Rejected",
                    message=f"Your interest in '{gig_title}' was rejected. The position has been filled.",
                    job_interest_id=other.id
                )
                db.add(rejected_notif)
        else:  # reject
            interest.status = InterestStatus.DECLINED
            decision = 'rejected'
        
        interest.updated_at = datetime.utcnow()
        
        # Create notification for the professional
        notif_title = "Interest Accepted!" if decision == 'accepted' else "Interest Rejected"
        notif_message = f"Your interest in '{gig_title}' has been {decision} by {institution_name}."
        
        professional_notification = Notification(
            user_id=professional_user_id,
            title=notif_title,
            message=notif_message,
            job_interest_id=interest.id
        )
        db.add(professional_notification)
        
        # 6. Commit DB transaction
        db.commit()
        
        # AFTER commit - emit Socket.IO notification to professional
        try:
            from app import socketio
            socketio.emit('interest_decision', {
                'gig_id': job.id,
                'gig_title': gig_title,
                'decision': decision,
                'institution_name': institution_name,
                'interest_id': interest_id,
                'message': notif_message
            }, room=f'professional_{interest.professional_id}')
            
            # Also emit to user room for broader compatibility
            socketio.emit('interest_decision', {
                'gig_id': job.id,
                'gig_title': gig_title,
                'decision': decision,
                'institution_name': institution_name,
                'interest_id': interest_id,
                'message': notif_message
            }, room=f'user_{professional_user_id}')
        except Exception as socket_error:
            # Log but don't fail - DB is already committed
            import logging
            logging.error(f"Socket.IO emission failed: {socket_error}")
        
        # Build response
        response_data = {
            'success': True,
            'message': f'Interest {decision} successfully',
            'decision': decision,
            'interest_id': interest_id
        }
        
        # Add chat_url if accepted
        if decision == 'accepted':
            response_data['chat_url'] = f'/messages/conversation/{professional_user_id}'
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.rollback()
        import logging
        logging.error(f"Error in respond_to_gig_interest: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# ============================================================================
# ============================================================================
# UNIFIED DASHBOARD ROUTE (Role-Aware)
# ============================================================================

@web_blueprint.route('/dashboard')
@login_required
def dashboard():
    """Unified dashboard that adapts based on active_role"""
    return render_template('unified_dashboard.html')


# ============================================================================
# INSTITUTION ADMIN DASHBOARD ROUTES
# ============================================================================

@web_blueprint.route('/institution/dashboard')
@login_required
@role_required('institution')
def institution_dashboard():
    """Institution Admin Dashboard - Overview with KPI metrics"""
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            flash('Institution profile not found', 'error')
            return redirect(url_for('web.profile'))
        
        # Calculate KPI metrics
        total_gigs = db.query(Job).filter(Job.institution_id == institution.id).count()
        active_gigs = db.query(Job).filter(
            Job.institution_id == institution.id,
            Job.status == JobStatus.OPEN
        ).count()
        closed_gigs = db.query(Job).filter(
            Job.institution_id == institution.id,
            Job.status.in_([JobStatus.CLOSED, JobStatus.COMPLETED])
        ).count()
        
        # Interest metrics
        all_interests = db.query(JobInterest).join(Job).filter(
            Job.institution_id == institution.id
        ).all()
        
        pending_interests = sum(1 for i in all_interests if i.status == InterestStatus.PENDING)
        accepted_interests = sum(1 for i in all_interests if i.status == InterestStatus.ACCEPTED)
        rejected_interests = sum(1 for i in all_interests if i.status == InterestStatus.DECLINED)
        
        # Calculate rates with proper zero checks
        total_responded = accepted_interests + rejected_interests
        accept_rate = round((accepted_interests / total_responded * 100), 1) if total_responded > 0 else 0
        response_rate = round((total_responded / len(all_interests) * 100), 1) if len(all_interests) > 0 else 0
        
        # Total unique professionals
        total_professionals = db.query(func.count(func.distinct(JobInterest.professional_id))).join(Job).filter(
            Job.institution_id == institution.id
        ).scalar() or 0
        
        # Payment metrics
        total_spent = db.query(func.sum(Payment.amount)).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        pending_payments = db.query(Payment).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.PENDING
        ).count()
        
        completed_payments = db.query(Payment).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.COMPLETED
        ).count()
        
        metrics = {
            'total_gigs': total_gigs,
            'active_gigs': active_gigs,
            'closed_gigs': closed_gigs,
            'pending_interests': pending_interests,
            'accepted_interests': accepted_interests,
            'rejected_interests': rejected_interests,
            'total_professionals': total_professionals,
            'accept_rate': accept_rate,
            'response_rate': response_rate,
            'total_spent': total_spent,
            'pending_payments': pending_payments,
            'completed_payments': completed_payments
        }
        
        # Recent interests
        recent_interests = db.query(JobInterest).join(Job).filter(
            Job.institution_id == institution.id
        ).order_by(desc(JobInterest.created_at)).limit(5).all()
        
        # Top performing gigs
        top_gigs = db.query(
            Job,
            func.count(JobInterest.id).label('interest_count')
        ).outerjoin(JobInterest).filter(
            Job.institution_id == institution.id
        ).group_by(Job.id).order_by(desc('interest_count')).limit(5).all()
        
        top_gigs_list = [{'title': job.title, 'status': job.status, 'interest_count': count} for job, count in top_gigs]
        
        # Get unread notification count for sidebar badge
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == session['user_id'],
            Notification.is_read == False
        ).count()
        
        return render_template('institution_overview.html',
                             active_section='overview',
                             pending_count=unread_notifications,
                             metrics=metrics,
                             recent_interests=recent_interests,
                             top_gigs=top_gigs_list)
    finally:
        db.close()

@web_blueprint.route('/institution/gigs')
@login_required
@role_required('institution')
def institution_gigs():
    """Institution Gigs Management Page"""
    return redirect(url_for('web.my_gigs'))

@web_blueprint.route('/institution/notifications')
@login_required
@role_required('institution')
def institution_notifications():
    """Institution Notifications Panel"""
    return redirect(url_for('web.notifications'))

@web_blueprint.route('/institution/analytics')
@login_required
@role_required('institution')
def institution_analytics():
    """Institution Analytics Section"""
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            flash('Institution profile not found', 'error')
            return redirect(url_for('web.profile'))
        
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Interest trends
        interests_by_day = db.query(
            func.date(JobInterest.created_at).label('date'),
            func.count(JobInterest.id).label('count')
        ).join(Job).filter(
            Job.institution_id == institution.id,
            JobInterest.created_at >= thirty_days_ago
        ).group_by(func.date(JobInterest.created_at)).all()
        
        # Status counts
        status_counts = db.query(
            JobInterest.status,
            func.count(JobInterest.id).label('count')
        ).join(Job).filter(
            Job.institution_id == institution.id
        ).group_by(JobInterest.status).all()
        
        # Top gigs
        top_gigs = db.query(
            Job.title,
            func.count(JobInterest.id).label('interest_count')
        ).outerjoin(JobInterest).filter(
            Job.institution_id == institution.id
        ).group_by(Job.id).order_by(desc('interest_count')).limit(10).all()
        
        # Get unread notification count for sidebar badge
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == session['user_id'],
            Notification.is_read == False
        ).count()
        
        analytics_data = {
            'interests_by_day': [{'date': str(date), 'count': count} for date, count in interests_by_day],
            'status_counts': [{'status': status.value, 'count': count} for status, count in status_counts],
            'top_gigs': [{'title': title, 'count': count} for title, count in top_gigs]
        }
        
        return render_template('institution_analytics.html',
                             active_section='analytics',
                             pending_count=unread_notifications,
                             analytics=analytics_data)
    finally:
        db.close()


@web_blueprint.route('/api/institution/analytics/export')
@login_required
@role_required('institution')
def export_institution_analytics_csv():
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            from flask import jsonify
            return jsonify({'error': 'Institution profile not found'}), 404

        from io import StringIO
        import csv
        from flask import Response
        from sqlalchemy.orm import aliased
        from sqlalchemy import and_
        from app.models.payment import Payment
        from app.models.user import User

        latest_payment_ts = db.query(
            Payment.gig_id.label('gig_id'),
            Payment.professional_id.label('professional_id'),
            Payment.institution_id.label('institution_id'),
            func.max(Payment.created_at).label('max_created_at')
        ).filter(
            Payment.institution_id == institution.id
        ).group_by(
            Payment.gig_id,
            Payment.professional_id,
            Payment.institution_id
        ).subquery()

        LatestPayment = aliased(Payment)

        rows = db.query(
            JobInterest,
            Job,
            Professional,
            User,
            LatestPayment
        ).join(
            Job, Job.id == JobInterest.job_id
        ).join(
            Professional, Professional.id == JobInterest.professional_id
        ).join(
            User, User.id == Professional.user_id
        ).outerjoin(
            latest_payment_ts,
            and_(
                latest_payment_ts.c.gig_id == JobInterest.job_id,
                latest_payment_ts.c.professional_id == JobInterest.professional_id,
                latest_payment_ts.c.institution_id == institution.id
            )
        ).outerjoin(
            LatestPayment,
            and_(
                LatestPayment.gig_id == latest_payment_ts.c.gig_id,
                LatestPayment.professional_id == latest_payment_ts.c.professional_id,
                LatestPayment.institution_id == latest_payment_ts.c.institution_id,
                LatestPayment.created_at == latest_payment_ts.c.max_created_at
            )
        ).filter(
            Job.institution_id == institution.id
        ).order_by(
            desc(JobInterest.created_at)
        ).all()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'date',
            'gig_title',
            'professional_name',
            'email',
            'telephone_no',
            'payment_paid',
            'payment_status'
        ])

        for interest, job, professional, user, payment in rows:
            payment_amount = ''
            payment_status = ''
            if payment:
                payment_amount = payment.amount
                payment_status = payment.status.value if payment.status else ''
            else:
                payment_status = 'unpaid'

            writer.writerow([
                interest.created_at.strftime('%Y-%m-%d %H:%M:%S') if interest.created_at else '',
                job.title if job else '',
                professional.full_name or '',
                user.email if user else '',
                professional.phone_number or '',
                payment_amount,
                payment_status
            ])

        csv_data = output.getvalue()
        filename = f"institution_analytics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    finally:
        db.close()

@web_blueprint.route('/institution/users')
@login_required
@role_required('institution')
def institution_users():
    """Institution User Management"""
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            flash('Institution profile not found', 'error')
            return redirect(url_for('web.profile'))
        
        # Get professionals who interacted with institution gigs
        from sqlalchemy import case
        professionals = db.query(
            Professional,
            func.count(JobInterest.id).label('total_interests'),
            func.sum(case((JobInterest.status == InterestStatus.ACCEPTED, 1), else_=0)).label('accepted_count'),
            func.sum(case((JobInterest.status == InterestStatus.DECLINED, 1), else_=0)).label('rejected_count'),
            func.max(JobInterest.created_at).label('last_activity')
        ).join(JobInterest).join(Job).filter(
            Job.institution_id == institution.id
        ).group_by(Professional.id).order_by(desc('last_activity')).all()
        
        professionals_list = []
        for prof, total, accepted, rejected, last_activity in professionals:
            # Defensive fallbacks (templates often do name[0] for avatars)
            email = None
            try:
                email = prof.user.email if prof.user else None
            except Exception:
                email = None

            name = (prof.full_name or (email or '')).strip() if prof else ''
            if not name:
                name = 'Unknown'

            professionals_list.append({
                'id': prof.id,
                'name': name,
                'email': email or '',
                'total_interests': total,
                'accepted_count': accepted or 0,
                'rejected_count': rejected or 0,
                'last_activity': last_activity
            })
        
        # Get unread notification count for sidebar badge
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == session['user_id'],
            Notification.is_read == False
        ).count()
        
        return render_template('institution_users.html',
                             active_section='users',
                             pending_count=unread_notifications,
                             professionals=professionals_list)
    finally:
        db.close()

@web_blueprint.route('/institution/payments')
@login_required
@role_required('institution')
def institution_payments():
    """Institution Payment Management Page"""
    from sqlalchemy.orm import joinedload
    from sqlalchemy import exists
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            flash('Institution profile not found', 'error')
            return redirect(url_for('web.profile'))
        
        # Get gigs awaiting payment (any gig that does not have a COMPLETED payment)
        unpaid_gigs = db.query(Job).options(
            joinedload(Job.assigned_professional)
        ).filter(
            Job.institution_id == institution.id,
            Job.assigned_professional_id.isnot(None),
            Job.status.in_([JobStatus.ASSIGNED, JobStatus.ACCEPTED, JobStatus.COMPLETED]),
            ~exists().where(
                (Payment.gig_id == Job.id) &
                (Payment.status == TransactionStatus.COMPLETED)
            )
        ).order_by(desc(Job.updated_at)).all()
        
        # Get payment history
        latest_payment_per_gig = db.query(
            Payment.gig_id.label('gig_id'),
            func.max(Payment.created_at).label('max_created_at')
        ).filter(
            Payment.institution_id == institution.id
        ).group_by(Payment.gig_id).subquery()

        payment_history = db.query(Payment).options(
            joinedload(Payment.gig),
            joinedload(Payment.professional)
        ).join(
            latest_payment_per_gig,
            (Payment.gig_id == latest_payment_per_gig.c.gig_id) &
            (Payment.created_at == latest_payment_per_gig.c.max_created_at)
        ).filter(
            Payment.institution_id == institution.id
        ).order_by(desc(Payment.created_at)).all()
        
        # Calculate summary stats
        total_spent = db.query(func.sum(Payment.amount)).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.COMPLETED
        ).scalar() or 0
        
        completed_count = db.query(Payment).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.COMPLETED
        ).count()
        
        pending_payments_count = db.query(Payment).filter(
            Payment.institution_id == institution.id,
            Payment.status == TransactionStatus.PENDING
        ).count()
        
        # Get unread notification count for sidebar badge
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == session['user_id'],
            Notification.is_read == False
        ).count()
        
        return render_template('institution_payments.html',
                             active_section='payments',
                             unpaid_gigs=unpaid_gigs,
                             payment_history=payment_history,
                             total_spent=total_spent,
                             completed_count=completed_count,
                             pending_count=unread_notifications,
                             pending_payments_count=pending_payments_count)
    finally:
        db.close()

@web_blueprint.route('/institution/professional/<int:professional_id>/history')
@login_required
@role_required('institution')
def professional_history(professional_id):
    """View professional interaction history with this institution"""
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            flash('Institution profile not found', 'error')
            return redirect(url_for('web.profile'))
        
        professional = db.query(Professional).filter(Professional.id == professional_id).first()
        if not professional:
            flash('Professional not found', 'error')
            return redirect(url_for('web.institution_users'))

        # Rating summary
        average_rating = db.query(func.avg(Rating.rating)).filter(
            Rating.professional_id == professional.id
        ).scalar() or 0

        total_ratings = db.query(func.count(Rating.id)).filter(
            Rating.professional_id == professional.id
        ).scalar() or 0

        requires_registration = (professional.profession_category in ['Health', 'Formal']) if professional.profession_category else False
        professional_is_verified = bool(requires_registration and professional.registration_number and professional.issuing_body)

        # Find most recent completed gig with this professional for rating
        rating_gig = db.query(Job).filter(
            Job.institution_id == institution.id,
            Job.assigned_professional_id == professional.id,
            Job.status == JobStatus.COMPLETED
        ).order_by(desc(Job.updated_at)).first()

        rating_gig_id = rating_gig.id if rating_gig else None
        already_rated = False
        if rating_gig_id:
            existing_rating = db.query(Rating).filter(
                Rating.gig_id == rating_gig_id,
                Rating.rater_id == session['user_id']
            ).first()
            already_rated = existing_rating is not None
        
        # Get all job interests from this professional for this institution's gigs
        interests = db.query(JobInterest).join(Job).filter(
            Job.institution_id == institution.id,
            JobInterest.professional_id == professional_id
        ).order_by(desc(JobInterest.created_at)).all()
        
        # Get unread notification count for sidebar badge
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == session['user_id'],
            Notification.is_read == False
        ).count()
        
        return render_template('professional_history.html',
                             active_section='users',
                             pending_count=unread_notifications,
                             professional=professional,
                             professional_is_verified=professional_is_verified,
                             average_rating=average_rating,
                             total_ratings=total_ratings,
                             rating_gig_id=rating_gig_id,
                             already_rated=already_rated,
                             interests=interests)
    finally:
        db.close()

@web_blueprint.route('/institution/settings')
@login_required
@role_required('institution')
def institution_settings():
    """Institution Settings Page"""
    return redirect(url_for('web.profile'))

@web_blueprint.route('/api/institution/metrics')
@login_required
@role_required('institution')
def get_institution_metrics():
    """API endpoint for real-time dashboard metrics"""
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.user_id == session['user_id']).first()
        if not institution:
            return jsonify({'error': 'Institution not found'}), 404
        
        total_gigs = db.query(Job).filter(Job.institution_id == institution.id).count()
        active_gigs = db.query(Job).filter(
            Job.institution_id == institution.id,
            Job.status == JobStatus.OPEN
        ).count()
        
        all_interests = db.query(JobInterest).join(Job).filter(
            Job.institution_id == institution.id
        ).all()
        
        pending_interests = sum(1 for i in all_interests if i.status == InterestStatus.PENDING)
        accepted_interests = sum(1 for i in all_interests if i.status == InterestStatus.ACCEPTED)
        rejected_interests = sum(1 for i in all_interests if i.status == InterestStatus.DECLINED)
        
        return jsonify({
            'metrics': {
                'total_gigs': total_gigs,
                'active_gigs': active_gigs,
                'pending_interests': pending_interests,
                'accepted_interests': accepted_interests,
                'rejected_interests': rejected_interests
            }
        })
    finally:
        db.close()

# ============================================================================
# ADMIN ROUTES (System Administrator)
# ============================================================================

@web_blueprint.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    """Admin view all users with documents"""
    db = SessionLocal()
    try:
        from sqlalchemy.orm import joinedload
        
        # Get all users with their documents
        users = db.query(User).options(
            joinedload(User.professional),
            joinedload(User.institution)
        ).order_by(desc(User.created_at)).all()
        
        # Get documents for each user
        user_documents = {}
        for user in users:
            docs = db.query(Document).filter(Document.user_id == user.id).all()
            user_documents[user.id] = docs
        
        return render_template('admin_users.html', users=users, user_documents=user_documents)
    finally:
        db.close()

@web_blueprint.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user_status(user_id):
    """Toggle user active status"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = not user.is_active
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
            'is_active': user.is_active
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_user_admin(user_id):
    """Admin delete user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Prevent deleting self
        if user.id == session['user_id']:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Delete related data
        if user.role == UserRole.PROFESSIONAL:
            professional = db.query(Professional).filter(Professional.user_id == user.id).first()
            if professional:
                db.query(JobInterest).filter(JobInterest.professional_id == professional.id).delete()
                db.delete(professional)
        elif user.role == UserRole.INSTITUTION:
            institution = db.query(Institution).filter(Institution.user_id == user.id).first()
            if institution:
                jobs = db.query(Job).filter(Job.institution_id == institution.id).all()
                for job in jobs:
                    db.query(JobInterest).filter(JobInterest.job_id == job.id).delete()
                    db.delete(job)
                db.delete(institution)
        
        # Delete notifications, messages, documents
        db.query(Notification).filter(Notification.user_id == user.id).delete()
        db.query(Message).filter((Message.sender_id == user.id) | (Message.receiver_id == user.id)).delete()
        db.query(Document).filter(Document.user_id == user.id).delete()
        
        db.delete(user)
        db.commit()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/admin/jobs')
@login_required
@role_required('admin')
def admin_jobs():
    """Admin view all jobs with full details"""
    db = SessionLocal()
    try:
        from sqlalchemy.orm import joinedload
        
        jobs = db.query(Job).options(
            joinedload(Job.institution),
            joinedload(Job.assigned_professional)
        ).order_by(desc(Job.created_at)).all()
        
        # Get interest counts for each job
        job_stats = {}
        for job in jobs:
            interests = db.query(JobInterest).filter(JobInterest.job_id == job.id).all()
            job_stats[job.id] = {
                'total_interests': len(interests),
                'pending': len([i for i in interests if i.status == InterestStatus.PENDING]),
                'accepted': len([i for i in interests if i.status == InterestStatus.ACCEPTED]),
                'declined': len([i for i in interests if i.status == InterestStatus.DECLINED])
            }
        
        return render_template('admin_jobs.html', jobs=jobs, job_stats=job_stats)
    finally:
        db.close()

@web_blueprint.route('/admin/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_job_admin(job_id):
    """Admin delete job"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        # Delete dependent records first to avoid FK constraint failures
        db.query(Payment).filter(Payment.gig_id == job.id).delete(synchronize_session=False)
        db.query(Rating).filter(Rating.gig_id == job.id).delete(synchronize_session=False)
        db.query(Message).filter(Message.job_id == job.id).delete(synchronize_session=False)

        # Interests tables (legacy + new)
        db.query(GigInterest).filter(GigInterest.job_id == job.id).delete(synchronize_session=False)
        db.query(JobInterest).filter(JobInterest.job_id == job.id).delete(synchronize_session=False)

        db.delete(job)
        db.commit()
        
        return jsonify({'success': True, 'message': 'Job deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@web_blueprint.route('/admin/payments')
@login_required
@role_required('admin')
def admin_payments():
    """Admin view all payments"""
    from sqlalchemy.orm import joinedload
    db = SessionLocal()
    try:
        latest_payment_per_gig = db.query(
            Payment.gig_id.label('gig_id'),
            func.max(Payment.created_at).label('max_created_at')
        ).group_by(Payment.gig_id).subquery()

        payments = db.query(Payment).options(
            joinedload(Payment.gig),
            joinedload(Payment.institution),
            joinedload(Payment.professional)
        ).join(
            latest_payment_per_gig,
            (Payment.gig_id == latest_payment_per_gig.c.gig_id) &
            (Payment.created_at == latest_payment_per_gig.c.max_created_at)
        ).order_by(desc(Payment.created_at)).all()
        return render_template('admin_payments.html', payments=payments)
    finally:
        db.close()

@web_blueprint.route('/admin/analytics')
@login_required
@role_required('admin')
def admin_analytics():
    """Admin system analytics with real data"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # User statistics
        total_users = db.query(User).count()
        professionals_count = db.query(User).filter(User.role == UserRole.PROFESSIONAL).count()
        institutions_count = db.query(User).filter(User.role == UserRole.INSTITUTION).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # Job statistics
        total_jobs = db.query(Job).count()
        active_jobs = db.query(Job).filter(Job.status == JobStatus.OPEN).count()
        completed_jobs = db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        
        # Interest statistics
        total_interests = db.query(JobInterest).count()
        pending_interests = db.query(JobInterest).filter(JobInterest.status == InterestStatus.PENDING).count()
        accepted_interests = db.query(JobInterest).filter(JobInterest.status == InterestStatus.ACCEPTED).count()
        
        # Document statistics
        total_documents = db.query(Document).count()
        verified_documents = db.query(Document).filter(Document.status == DocumentStatus.APPROVED).count()
        pending_documents = db.query(Document).filter(Document.status == DocumentStatus.PENDING).count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30d = db.query(User).filter(User.created_at >= thirty_days_ago).count()
        new_jobs_30d = db.query(Job).filter(Job.created_at >= thirty_days_ago).count()
        
        # Growth data for charts (last 7 days)
        daily_stats = []
        for i in range(7):
            day = datetime.utcnow() - timedelta(days=6-i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            users_count = db.query(User).filter(
                User.created_at >= day_start,
                User.created_at < day_end
            ).count()
            
            jobs_count = db.query(Job).filter(
                Job.created_at >= day_start,
                Job.created_at < day_end
            ).count()
            
            daily_stats.append({
                'date': day.strftime('%b %d'),
                'users': users_count,
                'jobs': jobs_count
            })
        
        analytics = {
            'users': {
                'total': total_users,
                'professionals': professionals_count,
                'institutions': institutions_count,
                'active': active_users,
                'new_30d': new_users_30d
            },
            'jobs': {
                'total': total_jobs,
                'active': active_jobs,
                'completed': completed_jobs,
                'new_30d': new_jobs_30d
            },
            'interests': {
                'total': total_interests,
                'pending': pending_interests,
                'accepted': accepted_interests
            },
            'documents': {
                'total': total_documents,
                'verified': verified_documents,
                'pending': pending_documents
            },
            'daily_stats': daily_stats
        }
        
        return render_template('admin_analytics.html', analytics=analytics)
    finally:
        db.close()

@web_blueprint.route('/admin/settings')
@login_required
@role_required('admin')
def admin_settings():
    """Admin system settings"""
    db = SessionLocal()
    try:
        # Get system configuration
        config = {
            'platform_name': 'QGig',
            'version': '1.0.0',
            'maintenance_mode': False,
            'allow_registrations': True,
            'require_email_verification': False
        }
        
        return render_template('admin_settings.html', config=config)
    finally:
        db.close()

@web_blueprint.route('/admin/settings/update', methods=['POST'])
@login_required
@role_required('admin')
def update_admin_settings():
    """Update admin settings"""
    data = request.get_json() if request.is_json else request.form
    return jsonify({'success': True, 'message': 'Settings updated successfully'})

