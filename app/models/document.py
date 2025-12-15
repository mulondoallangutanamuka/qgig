from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum

class DocumentStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class DocumentType(enum.Enum):
    NIN = "nin"
    CERTIFICATE = "certificate"
    LICENSE = "license"
    CV = "cv"
    PROFILE_PICTURE = "profile_picture"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=True, index=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    admin_notes = Column(Text, nullable=True)
    is_verified = Column(Integer, default=0, nullable=False)
    
    user = relationship("User", foreign_keys=[user_id], backref="documents")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
