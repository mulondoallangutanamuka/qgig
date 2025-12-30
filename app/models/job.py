from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum

class JobStatus(enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CLOSED = "closed"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=False)
    pay_amount = Column(Float, nullable=False)
    duration_hours = Column(Float)
    is_urgent = Column(Boolean, default=False)
    status = Column(Enum(JobStatus), default=JobStatus.OPEN, nullable=False)
    assigned_professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True, index=True)
    job_type = Column(String(100), nullable=True, index=True)
    sector = Column(String(100), nullable=True, index=True)
    
    institution = relationship("Institution", backref="jobs")
    assigned_professional = relationship("Professional", foreign_keys=[assigned_professional_id], backref="assigned_gigs")

class GigInterest(Base):
    __tablename__ = "gig_interests"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    job = relationship("Job", backref="interests")
    professional = relationship("Professional", backref="interests")
