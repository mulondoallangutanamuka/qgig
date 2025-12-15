"""
Reset Admin Password Script
"""
import bcrypt
from app.database import SessionLocal
from app.models.user import User, UserRole

def reset_admin_password():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        
        if not admin:
            print("No admin user found!")
            return
        
        new_password = "Admin@123"
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
        
        admin.password = hashed.decode()
        db.commit()
        
        print(f"✅ Admin password reset successfully!")
        print(f"Email: {admin.email}")
        print(f"Password: {new_password}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()
