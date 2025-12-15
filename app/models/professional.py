from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Professional(Base):
    __tablename__ = "professionals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    full_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    skills = Column(Text)
    bio = Column(Text)
    hourly_rate = Column(Float)
    daily_rate = Column(Float)
    location = Column(String(100))
    
    # Additional professional information
    education = Column(Text, nullable=True)
    certifications = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    specialization = Column(String(200), nullable=True)
    languages = Column(String(200), nullable=True)
    
    # Profession category and registration (for regulated professions)
    profession_category = Column(String(50), nullable=True)
    registration_number = Column(String(100), nullable=True)
    issuing_body = Column(String(200), nullable=True)
    
    # File uploads (legacy - will migrate to Document model)
    cv_file = Column(String(255), nullable=True)
    certificate_files = Column(Text, nullable=True)
    profile_picture = Column(String(255), nullable=True)
    
    user = relationship("User", back_populates="professional")
