from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum

class UserRole(enum.Enum):
    PROFESSIONAL = "professional"
    INSTITUTION = "institution"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True, default=UserRole.PROFESSIONAL)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    password_reset_token_hash = Column(String(128), nullable=True, index=True)
    password_reset_expires_at = Column(DateTime, nullable=True, index=True)
    professional = relationship("Professional", back_populates="user", uselist=False)
    institution = relationship("Institution", back_populates="user", uselist=False)
    user_roles = relationship("UserRoleAssignment", back_populates="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Flask-Login integration
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
