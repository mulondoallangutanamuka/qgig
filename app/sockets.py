"""
Socket.IO event handlers for real-time notifications
"""
from flask_socketio import emit, join_room, leave_room
from flask import session, request
from app.database import SessionLocal
from app.models.user import User
from app.models.institution import Institution
from app.models.professional import Professional
import logging

logger = logging.getLogger(__name__)

# Store user socket connections (user_id -> socket_id)
user_connections = {}

# Global socketio instance reference
_socketio = None

def set_socketio(socketio_instance):
    """Set the global socketio instance"""
    global _socketio
    _socketio = socketio_instance

def register_socketio_events(socketio_instance):
    """Register all socket.io event handlers"""
    
    @socketio_instance.on('connect')
    def handle_connect(auth=None):
        """Handle client connection"""
        logger.info("=== Socket.IO Connection Attempt ===")
        logger.info(f"Session data: {dict(session)}")
        
        # Check if user is authenticated via session or auth parameter
        user_id = session.get('user_id')
        
        # If no session, check auth parameter (for JWT-based connections)
        if not user_id and auth and isinstance(auth, dict):
            user_id = auth.get('user_id')
            if user_id:
                session['user_id'] = user_id
                logger.info(f"User {user_id} authenticated via auth parameter")
        
        if not user_id:
            logger.warning("Unauthenticated socket connection attempt rejected")
            return False  # Reject connection
        
        socket_id = request.sid
        
        # Store connection
        user_connections[user_id] = socket_id
        
        # Join user's personal room
        join_room(f'user_{user_id}')
        logger.info(f'User {user_id} joined room: user_{user_id}')
        
        # Get user details and join role-based rooms
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found in database")
                return False
            
            # Join role-based room
            if user.role.value == 'institution':
                institution = db.query(Institution).filter(Institution.user_id == user_id).first()
                if institution:
                    room_name = f'institution_{institution.id}'
                    join_room(room_name)
                    logger.info(f'✓ Institution user {user_id} joined room: {room_name}')
                    print(f'✓ Institution {institution.id} connected to room: {room_name}')
                    emit('connected', {
                        'user_id': user_id,
                        'role': 'institution',
                        'institution_id': institution.id,
                        'room': room_name,
                        'message': 'Connected to notification service'
                    })
                else:
                    logger.warning(f"Institution profile not found for user {user_id}")
                    emit('connected', {'user_id': user_id, 'message': 'Connected (no institution profile)'})
                    
            elif user.role.value == 'professional':
                professional = db.query(Professional).filter(Professional.user_id == user_id).first()
                if professional:
                    room_name = f'professional_{professional.id}'
                    join_room(room_name)
                    logger.info(f'✓ Professional user {user_id} joined room: {room_name}')
                    print(f'✓ Professional {professional.id} connected to room: {room_name}')
                    emit('connected', {
                        'user_id': user_id,
                        'role': 'professional',
                        'professional_id': professional.id,
                        'room': room_name,
                        'message': 'Connected to notification service'
                    })
                else:
                    logger.warning(f"Professional profile not found for user {user_id}")
                    emit('connected', {'user_id': user_id, 'message': 'Connected (no professional profile)'})
            else:
                # Admin or other roles
                logger.info(f'User {user_id} connected with role: {user.role.value}')
                emit('connected', {'user_id': user_id, 'role': user.role.value, 'message': 'Connected to notification service'})
            
        except Exception as e:
            logger.error(f'Error during socket connection setup: {e}', exc_info=True)
            emit('error', {'message': 'Connection error occurred'})
            return False
        finally:
            db.close()
        
        print(f'✓ User {user_id} connected with socket ID {socket_id}')

    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        if 'user_id' in session:
            user_id = session['user_id']
            
            # Remove connection
            if user_id in user_connections:
                del user_connections[user_id]
            
            # Leave user's personal room
            leave_room(f'user_{user_id}')
            
            logger.info(f'User {user_id} disconnected')
            print(f'User {user_id} disconnected')

    @socketio_instance.on('mark_notification_read')
    def handle_mark_read(data):
        """Handle marking notification as read"""
        if 'user_id' not in session:
            return
        
        from app.models.notification import Notification
        
        notification_id = data.get('notification_id')
        db = SessionLocal()
        
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == session['user_id']
            ).first()
            
            if notification:
                notification.is_read = True
                db.commit()
                
                emit('notification_read', {'notification_id': notification_id}, room=f'user_{session["user_id"]}')
        finally:
            db.close()

def emit_notification_to_user(user_id, event_name, data):
    """
    Helper function to emit notification to a specific user
    Can be called from anywhere in the app
    """
    if _socketio is None:
        logger.error(f"SocketIO not initialized, cannot send notification to user {user_id}")
        print(f"Warning: SocketIO not initialized, cannot send notification to user {user_id}")
        return
    
    room = f'user_{user_id}'
    logger.info(f"Emitting {event_name} to room {room}")
    logger.debug(f"Event data: {data}")
    
    try:
        _socketio.emit(event_name, data, room=room, namespace='/')
        logger.info(f"✓ Successfully emitted {event_name} to {room}")
    except Exception as e:
        logger.error(f"Failed to emit {event_name} to {room}: {e}", exc_info=True)

def send_interest_notification(institution_id, notification_data):
    """Send real-time notification when professional shows interest"""
    if _socketio is None:
        logger.error(f"SocketIO not initialized, cannot send interest notification")
        return
    
    # Emit to institution-specific room
    room = f'institution_{institution_id}'
    logger.info(f"=== Sending Interest Notification ===")
    logger.info(f"Target room: {room}")
    logger.info(f"Data: {notification_data}")
    
    try:
        _socketio.emit('job_interest_sent', notification_data, room=room, namespace='/')
        logger.info(f"✓ Interest notification sent to {room}")
        print(f"✓ Socket.IO: Sent job_interest_sent to {room}")
    except Exception as e:
        logger.error(f"Failed to send interest notification to {room}: {e}", exc_info=True)
        print(f"✗ Socket.IO: Failed to send to {room}: {e}")

def send_acceptance_notification(professional_user_id, notification_data):
    """Send real-time notification when institution accepts interest"""
    emit_notification_to_user(professional_user_id, 'interest_accepted', notification_data)

def send_rejection_notification(professional_user_id, notification_data):
    """Send real-time notification when institution rejects interest"""
    emit_notification_to_user(professional_user_id, 'interest_rejected', notification_data)

def send_message_notification(receiver_user_id, message_data):
    """Send real-time notification when a new message is received"""
    if not _socketio:
        logger.warning("SocketIO not initialized, cannot send message notification")
        return
    
    room = f'user_{receiver_user_id}'
    logger.info(f"=== Sending Message Notification ===")
    logger.info(f"Target room: {room}")
    logger.info(f"Data: {message_data}")
    
    try:
        _socketio.emit('new_message', message_data, room=room, namespace='/')
        logger.info(f"✓ Message notification sent to {room}")
        print(f"✓ Socket.IO: Sent new_message to {room}")
    except Exception as e:
        logger.error(f"Failed to send message notification to {room}: {e}", exc_info=True)
        print(f"✗ Socket.IO: Failed to send message to {room}: {e}")
