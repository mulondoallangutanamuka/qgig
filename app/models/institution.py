from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    institution_name = Column(String(100), nullable=True)
    description = Column(Text)
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    location = Column(String(100))
    
    user = relationship("User", back_populates="institution")
