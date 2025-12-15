from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum

class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    gig_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    
    pesapal_order_tracking_id = Column(String, unique=True, nullable=True, index=True)
    pesapal_merchant_reference = Column(String, unique=True, nullable=False, index=True)
    pesapal_transaction_id = Column(String, nullable=True)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False, index=True)
    payment_method = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    gig = relationship("Job", backref="payments")
    institution = relationship("Institution", backref="payments")
    professional = relationship("Professional", backref="payments_received")
