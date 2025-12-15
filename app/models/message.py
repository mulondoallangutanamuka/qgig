from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class MessageStatus(enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sender and Receiver
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Related to a specific gig/job interest
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
    job_interest_id = Column(Integer, ForeignKey("job_interests.id"), nullable=True, index=True)
    
    # Message content
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    
    # Status tracking
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.SENT, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Soft delete
    is_deleted_by_sender = Column(Boolean, default=False, nullable=False)
    is_deleted_by_receiver = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_messages")
    job = relationship("Job", backref="messages")
    job_interest = relationship("JobInterest", backref="messages")
    
    def mark_as_read(self):
        """Mark message as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        self.status = MessageStatus.READ
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'sender_email': self.sender.email if self.sender else None,
            'receiver_email': self.receiver.email if self.receiver else None,
            'job_id': self.job_id,
            'job_interest_id': self.job_interest_id,
            'subject': self.subject,
            'content': self.content,
            'status': self.status.value,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
