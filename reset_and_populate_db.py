"""
Reset database and populate with meaningful test data
"""
import os
from datetime import datetime, timedelta
import bcrypt
from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.job import Job, JobStatus
from app.models.job_interest import JobInterest, InterestStatus
from app.models.notification import Notification
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.payment import Payment, TransactionStatus

def hash_password(password):
    """Hash password using bcrypt to match login verification"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def reset_database():
    """Drop all tables and recreate them"""
    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("🔨 Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset complete!\n")

def populate_test_data():
    """Populate database with meaningful test data"""
    db = SessionLocal()
    
    try:
        print("📝 Creating test data...\n")
        
        # ===== USERS =====
        print("👥 Creating users...")
        
        # Admin user
        admin_user = User(
            email="admin@qgig.com",
            password=hash_password("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin_user)
        
        # Professional users
        prof_users = [
            User(email="sarah.nurse@gmail.com", password=hash_password("password123"), role=UserRole.PROFESSIONAL),
            User(email="john.plumber@gmail.com", password=hash_password("password123"), role=UserRole.PROFESSIONAL),
            User(email="mary.teacher@gmail.com", password=hash_password("password123"), role=UserRole.PROFESSIONAL),
            User(email="david.electrician@gmail.com", password=hash_password("password123"), role=UserRole.PROFESSIONAL),
        ]
        for user in prof_users:
            db.add(user)
        
        # Institution users
        inst_users = [
            User(email="nairobi.hospital@hospital.com", password=hash_password("password123"), role=UserRole.INSTITUTION),
            User(email="kampala.school@school.com", password=hash_password("password123"), role=UserRole.INSTITUTION),
            User(email="mombasa.hotel@hotel.com", password=hash_password("password123"), role=UserRole.INSTITUTION),
        ]
        for user in inst_users:
            db.add(user)
        
        db.commit()
        print(f"✅ Created {len(prof_users)} professionals, {len(inst_users)} institutions, 1 admin\n")
        
        # ===== PROFESSIONALS =====
        print("👨‍⚕️ Creating professional profiles...")
        
        professionals_data = [
            {
                "user": prof_users[0],
                "full_name": "Sarah Nakato",
                "phone_number": "+256700123456",
                "location": "Kampala, Uganda",
                "profession_category": "Health",
                "specialization": "Registered Nurse",
                "skills": "Patient care, IV administration, Emergency response, Vital signs monitoring",
                "bio": "Experienced registered nurse with 5 years in emergency care and patient management.",
                "hourly_rate": 50000,
                "daily_rate": 350000,
                "registration_number": "NUR-2019-12345",
                "issuing_body": "Uganda Nurses and Midwives Council",
                "experience": "5 years at Mulago Hospital Emergency Department",
                "education": "Bachelor of Nursing Science - Makerere University",
                "certifications": "BLS, ACLS, Trauma Nursing"
            },
            {
                "user": prof_users[1],
                "full_name": "John Omondi",
                "phone_number": "+254722334455",
                "location": "Nairobi, Kenya",
                "profession_category": "Informal",
                "specialization": "Plumber",
                "skills": "Pipe installation, Leak repair, Drainage systems, Water heater installation",
                "bio": "Professional plumber with expertise in residential and commercial plumbing.",
                "hourly_rate": 30000,
                "daily_rate": 200000,
                "experience": "8 years in plumbing services",
                "education": "Technical Training - Nairobi Technical Institute"
            },
            {
                "user": prof_users[2],
                "full_name": "Mary Achieng",
                "phone_number": "+254733445566",
                "location": "Kisumu, Kenya",
                "profession_category": "Formal",
                "specialization": "Primary School Teacher",
                "skills": "Curriculum development, Classroom management, Student assessment, English & Mathematics",
                "bio": "Dedicated primary school teacher passionate about early childhood education.",
                "hourly_rate": 40000,
                "daily_rate": 280000,
                "registration_number": "TSC-2018-67890",
                "issuing_body": "Teachers Service Commission",
                "experience": "6 years teaching primary school",
                "education": "Bachelor of Education - Kenyatta University",
                "certifications": "Primary Education Certificate, ICT in Education"
            },
            {
                "user": prof_users[3],
                "full_name": "David Musoke",
                "phone_number": "+256701234567",
                "location": "Entebbe, Uganda",
                "profession_category": "Informal",
                "specialization": "Electrician",
                "skills": "Electrical wiring, Circuit installation, Fault diagnosis, Solar panel installation",
                "bio": "Certified electrician specializing in residential and commercial electrical work.",
                "hourly_rate": 35000,
                "daily_rate": 250000,
                "experience": "7 years in electrical services",
                "education": "Electrical Engineering Diploma - Uganda Technical College"
            }
        ]
        
        professionals = []
        for data in professionals_data:
            prof = Professional(**data)
            db.add(prof)
            professionals.append(prof)
        
        db.commit()
        print(f"✅ Created {len(professionals)} professional profiles\n")
        
        # ===== INSTITUTIONS =====
        print("🏢 Creating institution profiles...")
        
        institutions_data = [
            {
                "user": inst_users[0],
                "institution_name": "Nairobi General Hospital",
                "contact_email": "hr@nairobihospital.com",
                "contact_phone": "+254720111222",
                "location": "Nairobi, Kenya",
                "description": "Leading healthcare facility providing comprehensive medical services."
            },
            {
                "user": inst_users[1],
                "institution_name": "Kampala International School",
                "contact_email": "admin@kampalais.com",
                "contact_phone": "+256702333444",
                "location": "Kampala, Uganda",
                "description": "Premier international school offering quality education from kindergarten to high school."
            },
            {
                "user": inst_users[2],
                "institution_name": "Mombasa Beach Resort",
                "contact_email": "jobs@mombasaresort.com",
                "contact_phone": "+254721555666",
                "location": "Mombasa, Kenya",
                "description": "Luxury beach resort offering world-class hospitality services."
            }
        ]
        
        institutions = []
        for data in institutions_data:
            inst = Institution(**data)
            db.add(inst)
            institutions.append(inst)
        
        db.commit()
        print(f"✅ Created {len(institutions)} institution profiles\n")
        
        # ===== JOBS =====
        print("💼 Creating job postings...")
        
        jobs_data = [
            {
                "institution": institutions[0],
                "title": "Emergency Room Nurse - Night Shift",
                "description": "Seeking experienced registered nurse for emergency department night shift. Must be able to handle high-pressure situations and provide excellent patient care.",
                "location": "Nairobi General Hospital, Nairobi",
                "job_type": "Part-time",
                "sector": "Health",
                "pay_amount": 350000,
                "duration_hours": 8,
                "is_urgent": True,
                "status": JobStatus.OPEN
            },
            {
                "institution": institutions[1],
                "title": "Substitute Teacher - Mathematics",
                "description": "Need a qualified teacher to cover mathematics classes for primary 5 and 6 students for 2 weeks.",
                "location": "Kampala International School, Kampala",
                "job_type": "Temporary",
                "sector": "Education",
                "pay_amount": 280000,
                "duration_hours": 6,
                "is_urgent": False,
                "status": JobStatus.OPEN
            },
            {
                "institution": institutions[2],
                "title": "Maintenance Electrician",
                "description": "Required: Experienced electrician for hotel maintenance. Must handle electrical repairs, installations, and emergency fixes.",
                "location": "Mombasa Beach Resort, Mombasa",
                "job_type": "Contract",
                "sector": "Hospitality",
                "pay_amount": 250000,
                "duration_hours": 8,
                "is_urgent": True,
                "status": JobStatus.OPEN
            },
            {
                "institution": institutions[2],
                "title": "Plumbing Repairs - Guest Rooms",
                "description": "Need professional plumber to fix plumbing issues in 15 guest rooms. Immediate start required.",
                "location": "Mombasa Beach Resort, Mombasa",
                "job_type": "One-time",
                "sector": "Hospitality",
                "pay_amount": 200000,
                "duration_hours": 10,
                "is_urgent": True,
                "status": JobStatus.OPEN
            },
            {
                "institution": institutions[0],
                "title": "Medical Assistant - Outpatient",
                "description": "Part-time medical assistant needed for outpatient department. Basic medical knowledge required.",
                "location": "Nairobi General Hospital, Nairobi",
                "job_type": "Part-time",
                "sector": "Health",
                "pay_amount": 180000,
                "duration_hours": 6,
                "is_urgent": False,
                "status": JobStatus.ASSIGNED
            }
        ]
        
        jobs = []
        for data in jobs_data:
            job = Job(**data)
            db.add(job)
            jobs.append(job)
        
        db.commit()
        print(f"✅ Created {len(jobs)} job postings\n")
        
        # ===== JOB INTERESTS =====
        print("✋ Creating job interests...")
        
        interests_data = [
            {"job": jobs[0], "professional": professionals[0], "status": InterestStatus.PENDING},  # Sarah -> ER Nurse
            {"job": jobs[1], "professional": professionals[2], "status": InterestStatus.PENDING},  # Mary -> Teacher
            {"job": jobs[2], "professional": professionals[3], "status": InterestStatus.PENDING},  # David -> Electrician
            {"job": jobs[3], "professional": professionals[1], "status": InterestStatus.PENDING},  # John -> Plumber
            {"job": jobs[4], "professional": professionals[0], "status": InterestStatus.ACCEPTED},  # Sarah -> Medical Assistant (assigned)
        ]
        
        interests = []
        for data in interests_data:
            interest = JobInterest(**data)
            db.add(interest)
            interests.append(interest)
        
        db.commit()
        print(f"✅ Created {len(interests)} job interests\n")
        
        # ===== NOTIFICATIONS =====
        print("🔔 Creating notifications...")
        
        notifications_data = [
            {
                "user": inst_users[0],
                "title": "New Interest in Your Job",
                "message": f"{professionals[0].full_name} has expressed interest in your job: {jobs[0].title}",
                "job_interest": interests[0]
            },
            {
                "user": inst_users[1],
                "title": "New Interest in Your Job",
                "message": f"{professionals[2].full_name} has expressed interest in your job: {jobs[1].title}",
                "job_interest": interests[1]
            },
            {
                "user": inst_users[2],
                "title": "New Interest in Your Job",
                "message": f"{professionals[3].full_name} has expressed interest in your job: {jobs[2].title}",
                "job_interest": interests[2]
            },
            {
                "user": inst_users[2],
                "title": "New Interest in Your Job",
                "message": f"{professionals[1].full_name} has expressed interest in your job: {jobs[3].title}",
                "job_interest": interests[3]
            },
        ]
        
        for data in notifications_data:
            notif = Notification(**data)
            db.add(notif)
        
        db.commit()
        print(f"✅ Created {len(notifications_data)} notifications\n")
        
        # ===== DOCUMENTS =====
        print("📄 Creating sample documents...")
        
        # Note: These are placeholder paths - actual files would need to be uploaded
        documents_data = [
            {
                "user_id": prof_users[0].id,
                "professional_id": professionals[0].id,
                "document_type": DocumentType.CV,
                "file_path": "/static/uploads/professionals/sample_cv_sarah.pdf",
                "file_name": "sarah_nakato_cv.pdf",
                "file_size": 245000,
                "mime_type": "application/pdf",
                "status": DocumentStatus.APPROVED
            },
            {
                "user_id": prof_users[0].id,
                "professional_id": professionals[0].id,
                "document_type": DocumentType.CERTIFICATE,
                "file_path": "/static/uploads/professionals/sample_cert_nursing.pdf",
                "file_name": "nursing_registration.pdf",
                "file_size": 180000,
                "mime_type": "application/pdf",
                "status": DocumentStatus.APPROVED
            },
        ]
        
        for data in documents_data:
            doc = Document(**data)
            db.add(doc)
        
        db.commit()
        print(f"✅ Created {len(documents_data)} sample documents\n")
        
        print("=" * 60)
        print("✅ DATABASE POPULATED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📊 Summary:")
        print(f"   Users: {len(prof_users) + len(inst_users) + 1}")
        print(f"   Professionals: {len(professionals)}")
        print(f"   Institutions: {len(institutions)}")
        print(f"   Jobs: {len(jobs)}")
        print(f"   Job Interests: {len(interests)}")
        print(f"   Notifications: {len(notifications_data)}")
        print(f"   Documents: {len(documents_data)}")
        print("\n🔑 Login Credentials:")
        print("   Admin: admin@qgig.com / admin123")
        print("   Professional: sarah.nurse@gmail.com / password123")
        print("   Professional: john.plumber@gmail.com / password123")
        print("   Professional: mary.teacher@gmail.com / password123")
        print("   Professional: david.electrician@gmail.com / password123")
        print("   Institution: nairobi.hospital@hospital.com / password123")
        print("   Institution: kampala.school@school.com / password123")
        print("   Institution: mombasa.hotel@hotel.com / password123")
        print("\n" + "=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔄 QGIG DATABASE RESET & POPULATION")
    print("=" * 60 + "\n")
    
    confirm = input("⚠️  This will DELETE ALL existing data. Continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        reset_database()
        populate_test_data()
    else:
        print("\n❌ Operation cancelled.")
