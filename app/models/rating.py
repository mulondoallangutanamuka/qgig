from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    gig_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False, index=True)
    rater_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rated_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    rating = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    gig = relationship("Job", backref="ratings")
    institution = relationship("Institution", foreign_keys=[institution_id], backref="ratings_given")
    professional = relationship("Professional", foreign_keys=[professional_id], backref="ratings_received")
    rater = relationship("User", foreign_keys=[rater_id], backref="ratings_given")
    rated = relationship("User", foreign_keys=[rated_id], backref="ratings_received")
    
    __table_args__ = (
        UniqueConstraint('gig_id', 'rater_id', name='unique_rating_per_gig'),
    )
