"""
Create Admin User Script
Creates an admin user for the QGIG platform
"""
import bcrypt
from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole

def create_admin_user():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.email}")
            return
        
        admin_email = "admin@qgig.com"
        admin_password = "Admin@123"
        
        hashed = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt())
        
        admin_user = User(
            email=admin_email,
            password=hashed.decode(),
            role=UserRole.ADMIN,
            is_active=True,
            username="admin"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("=" * 60)
        print("✅ Admin user created successfully!")
        print("=" * 60)
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print(f"User ID: {admin_user.id}")
        print("=" * 60)
        print("⚠️  IMPORTANT: Change the password after first login!")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
