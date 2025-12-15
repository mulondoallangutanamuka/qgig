from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from sqlalchemy import or_, and_, func, desc, case
from sqlalchemy.orm import joinedload
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.message import Message, MessageStatus
from app.models.job import Job
from app.models.job_interest import JobInterest
from app.models.professional import Professional
from app.models.institution import Institution
from datetime import datetime
from functools import wraps

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('web.login'))
        return f(*args, **kwargs)
    return decorated_function

messages_blueprint = Blueprint('messages', __name__, url_prefix='/messages')

@messages_blueprint.context_processor
def inject_user():
    """Inject current_user into all message templates"""
    from app.models.notification import Notification
    from app.models.document import Document, DocumentType
    
    current_user = None
    notification_count = 0
    
    if 'user_id' in session:
        db = SessionLocal()
        try:
            current_user = db.query(User).filter(User.id == session['user_id']).first()
            
            # Get unread notification count
            notification_count = db.query(Notification).filter(
                Notification.user_id == session['user_id'],
                Notification.is_read == False
            ).count()
            
            # Add profile picture
            if current_user:
                if current_user.role == UserRole.PROFESSIONAL:
                    prof = db.query(Professional).filter(Professional.user_id == current_user.id).first()
                    if prof:
                        profile_pic = db.query(Document).filter(
                            Document.professional_id == prof.id,
                            Document.document_type == DocumentType.PROFILE_PICTURE
                        ).first()
                        current_user.profile_picture = profile_pic.file_path if profile_pic else None
                    else:
                        current_user.profile_picture = None
                elif current_user.role == UserRole.INSTITUTION:
                    current_user.profile_picture = None
                else:
                    current_user.profile_picture = None
        finally:
            db.close()
    
    return dict(
        current_user=current_user,
        notification_count=notification_count,
        unread_count=notification_count
    )

@messages_blueprint.route('/inbox')
@login_required
def inbox():
    """Display user's message inbox with conversations"""
    db = SessionLocal()
    try:
        user_id = session['user_id']
        user = db.query(User).filter(User.id == user_id).first()
        
        # Get all messages involving this user
        all_messages = db.query(Message).filter(
            or_(
                and_(Message.sender_id == user_id, Message.is_deleted_by_sender == False),
                and_(Message.receiver_id == user_id, Message.is_deleted_by_receiver == False)
            )
        ).options(
            joinedload(Message.sender),
            joinedload(Message.receiver),
            joinedload(Message.job)
        ).order_by(desc(Message.created_at)).all()
        
        # Group by conversation partner (other user)
        conversations_dict = {}
        for msg in all_messages:
            other_user_id = msg.sender_id if msg.sender_id != user_id else msg.receiver_id
            if other_user_id not in conversations_dict:
                conversations_dict[other_user_id] = msg
        
        # Convert to list
        conversations = list(conversations_dict.values())
        
        # Get unread count per conversation
        conversation_data = []
        for msg in conversations:
            other_user = msg.sender if msg.sender_id != user_id else msg.receiver
            
            # Count unread messages from this conversation
            unread_count = db.query(Message).filter(
                Message.sender_id == other_user.id,
                Message.receiver_id == user_id,
                Message.is_read == False,
                Message.is_deleted_by_receiver == False
            ).count()
            
            # Get other user's profile info
            profile_name = None
            if other_user.role == UserRole.PROFESSIONAL:
                prof = db.query(Professional).filter(Professional.user_id == other_user.id).first()
                profile_name = prof.full_name if prof and prof.full_name else other_user.email
            elif other_user.role == UserRole.INSTITUTION:
                inst = db.query(Institution).filter(Institution.user_id == other_user.id).first()
                profile_name = inst.institution_name if inst and inst.institution_name else other_user.email
            else:
                profile_name = other_user.email
            
            conversation_data.append({
                'other_user': other_user,
                'profile_name': profile_name,
                'last_message': msg,
                'unread_count': unread_count,
                'job': msg.job
            })
        
        # Get total unread count
        total_unread = db.query(Message).filter(
            Message.receiver_id == user_id,
            Message.is_read == False,
            Message.is_deleted_by_receiver == False
        ).count()
        
        return render_template('messages_inbox.html',
                             conversations=conversation_data,
                             total_unread=total_unread)
    finally:
        db.close()

@messages_blueprint.route('/conversation/<int:other_user_id>')
@login_required
def conversation(other_user_id):
    """View conversation with a specific user"""
    db = SessionLocal()
    try:
        user_id = session['user_id']
        user = db.query(User).filter(User.id == user_id).first()
        other_user = db.query(User).filter(User.id == other_user_id).first()
        
        if not other_user:
            flash('User not found', 'error')
            return redirect(url_for('messages.inbox'))
        
        # Get all messages between these two users
        messages = db.query(Message).filter(
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == other_user_id, Message.is_deleted_by_sender == False),
                and_(Message.sender_id == other_user_id, Message.receiver_id == user_id, Message.is_deleted_by_receiver == False)
            )
        ).options(
            joinedload(Message.job),
            joinedload(Message.job_interest)
        ).order_by(Message.created_at).all()
        
        # Mark all received messages as read
        unread_messages = [m for m in messages if m.receiver_id == user_id and not m.is_read]
        for msg in unread_messages:
            msg.mark_as_read()
        
        if unread_messages:
            db.commit()
        
        # Get other user's profile info
        profile_name = None
        profile_info = None
        if other_user.role == UserRole.PROFESSIONAL:
            prof = db.query(Professional).filter(Professional.user_id == other_user.id).first()
            profile_name = prof.full_name if prof and prof.full_name else other_user.email
            profile_info = prof
        elif other_user.role == UserRole.INSTITUTION:
            inst = db.query(Institution).filter(Institution.user_id == other_user.id).first()
            profile_name = inst.institution_name if inst and inst.institution_name else other_user.email
            profile_info = inst
        else:
            profile_name = other_user.email
        
        # Get related job if any
        related_job = None
        if messages:
            for msg in reversed(messages):
                if msg.job_id:
                    related_job = msg.job
                    break
        
        return render_template('messages_conversation.html',
                             messages=messages,
                             other_user=other_user,
                             profile_name=profile_name,
                             profile_info=profile_info,
                             related_job=related_job)
    finally:
        db.close()

@messages_blueprint.route('/send', methods=['POST'])
@login_required
def send_message():
    """Send a new message"""
    db = SessionLocal()
    try:
        user_id = session['user_id']
        data = request.get_json() if request.is_json else request.form
        
        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()
        subject = data.get('subject', '').strip()
        job_id = data.get('job_id')
        job_interest_id = data.get('job_interest_id')
        
        if not receiver_id or not content:
            return jsonify({'error': 'Receiver and content are required'}), 400
        
        # Verify receiver exists
        receiver = db.query(User).filter(User.id == receiver_id).first()
        if not receiver:
            return jsonify({'error': 'Receiver not found'}), 404
        
        # Create message
        message = Message(
            sender_id=user_id,
            receiver_id=receiver_id,
            content=content,
            subject=subject if subject else None,
            job_id=job_id if job_id else None,
            job_interest_id=job_interest_id if job_interest_id else None,
            status=MessageStatus.SENT
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Emit socket event for real-time delivery
        from app.sockets import send_message_notification
        send_message_notification(receiver_id, {
            'message_id': message.id,
            'sender_id': user_id,
            'content': content,
            'created_at': message.created_at.isoformat(),
            'job_id': job_id
        })
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': message.to_dict()
            }), 201
        else:
            flash('Message sent successfully', 'success')
            return redirect(url_for('messages.conversation', other_user_id=receiver_id))
    
    except Exception as e:
        db.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error sending message: {str(e)}', 'error')
            return redirect(url_for('messages.inbox'))
    finally:
        db.close()

@messages_blueprint.route('/api/unread-count')
@login_required
def unread_count():
    """Get unread message count for current user"""
    db = SessionLocal()
    try:
        user_id = session['user_id']
        count = db.query(Message).filter(
            Message.receiver_id == user_id,
            Message.is_read == False,
            Message.is_deleted_by_receiver == False
        ).count()
        
        return jsonify({'unread_count': count})
    finally:
        db.close()

@messages_blueprint.route('/mark-read/<int:message_id>', methods=['POST'])
@login_required
def mark_read(message_id):
    """Mark a specific message as read"""
    db = SessionLocal()
    try:
        user_id = session['user_id']
        message = db.query(Message).filter(
            Message.id == message_id,
            Message.receiver_id == user_id
        ).first()
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        message.mark_as_read()
        db.commit()
        
        return jsonify({'success': True})
    finally:
        db.close()

@messages_blueprint.route('/delete/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    """Soft delete a message"""
    db = SessionLocal()
    try:
        user_id = session['user_id']
        message = db.query(Message).filter(Message.id == message_id).first()
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Soft delete based on user role
        if message.sender_id == user_id:
            message.is_deleted_by_sender = True
        elif message.receiver_id == user_id:
            message.is_deleted_by_receiver = True
        else:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.commit()
        
        flash('Message deleted', 'success')
        return redirect(url_for('messages.inbox'))
    finally:
        db.close()

@messages_blueprint.route('/compose')
@login_required
def compose():
    """Show compose message form"""
    db = SessionLocal()
    try:
        # Get receiver_id and job_id from query params if provided
        receiver_id = request.args.get('receiver_id')
        job_id = request.args.get('job_id')
        
        receiver = None
        job = None
        
        if receiver_id:
            receiver = db.query(User).filter(User.id == receiver_id).first()
        
        if job_id:
            job = db.query(Job).filter(Job.id == job_id).first()
        
        return render_template('messages_compose.html',
                             receiver=receiver,
                             job=job)
    finally:
        db.close()
