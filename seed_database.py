"""
Database seeder script to populate the database with sample data
Run this script to add sample users, gigs, and other data for testing
"""

from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.job import Job, JobStatus, GigInterest
from app.models.payment import Payment, TransactionStatus
from app.models.rating import Rating
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.notification import Notification
from app.models.job_interest import JobInterest, InterestStatus
import bcrypt
from datetime import datetime, timedelta
import random

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_database():
    db = SessionLocal()
    
    try:
        print("🌱 Starting database seeding...")
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        db.query(Rating).delete()
        db.query(Payment).delete()
        db.query(GigInterest).delete()
        db.query(Job).delete()
        db.query(Document).delete()
        db.query(Professional).delete()
        db.query(Institution).delete()
        db.query(User).delete()
        db.commit()
        
        # Create Admin User
        print("Creating admin user...")
        admin_user = User(
            email="admin@qgig.com",
            password=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        
        # Create Professional Users
        print("Creating professional users...")
        professionals_data = [
            {
                "email": "sarah.nurse@gmail.com",
                "password": "password123",
                "name": "Sarah Mwangi",
                "skills": "Registered Nurse, ICU Experience, Patient Care",
                "bio": "Experienced registered nurse with 5 years in critical care. Passionate about providing quality healthcare.",
                "hourly_rate": 1500,
                "daily_rate": 10000,
                "location": "Nairobi"
            },
            {
                "email": "john.doctor@gmail.com",
                "password": "password123",
                "name": "Dr. John Kamau",
                "skills": "General Practitioner, Emergency Medicine, Diagnostics",
                "bio": "General practitioner with expertise in emergency medicine and patient diagnostics.",
                "hourly_rate": 3000,
                "daily_rate": 20000,
                "location": "Mombasa"
            },
            {
                "email": "mary.caregiver@gmail.com",
                "password": "password123",
                "name": "Mary Akinyi",
                "skills": "Elderly Care, Home Nursing, Medication Management",
                "bio": "Compassionate caregiver specializing in elderly care and home nursing services.",
                "hourly_rate": 800,
                "daily_rate": 5000,
                "location": "Kisumu"
            },
            {
                "email": "peter.paramedic@gmail.com",
                "password": "password123",
                "name": "Peter Ochieng",
                "skills": "Paramedic, First Aid, Emergency Response",
                "bio": "Certified paramedic with quick response skills and emergency medical training.",
                "hourly_rate": 1200,
                "daily_rate": 8000,
                "location": "Nakuru"
            },
            {
                "email": "grace.therapist@gmail.com",
                "password": "password123",
                "name": "Grace Wanjiru",
                "skills": "Physical Therapy, Rehabilitation, Sports Medicine",
                "bio": "Licensed physical therapist helping patients recover and regain mobility.",
                "hourly_rate": 2000,
                "daily_rate": 12000,
                "location": "Nairobi"
            }
        ]
        
        professional_users = []
        for prof_data in professionals_data:
            user = User(
                email=prof_data["email"],
                password=hash_password(prof_data["password"]),
                role=UserRole.PROFESSIONAL,
                is_active=True
            )
            db.add(user)
            db.flush()
            
            professional = Professional(
                user_id=user.id,
                full_name=prof_data["name"],
                skills=prof_data["skills"],
                bio=prof_data["bio"],
                hourly_rate=prof_data["hourly_rate"],
                daily_rate=prof_data["daily_rate"],
                location=prof_data["location"]
            )
            db.add(professional)
            professional_users.append((user, professional))
        
        db.commit()
        print(f"✅ Created {len(professional_users)} professional users")
        
        # Create Institution Users
        print("Creating institution users...")
        institutions_data = [
            {
                "email": "nairobi.hospital@gmail.com",
                "password": "password123",
                "name": "Nairobi General Hospital",
                "description": "Leading healthcare facility providing comprehensive medical services to the community.",
                "contact_email": "hr@nairobihospital.co.ke",
                "contact_phone": "+254 700 111 222",
                "location": "Nairobi CBD"
            },
            {
                "email": "mombasa.clinic@gmail.com",
                "password": "password123",
                "name": "Mombasa Medical Clinic",
                "description": "Modern clinic offering quality healthcare services with experienced medical professionals.",
                "contact_email": "info@mombasaclinic.co.ke",
                "contact_phone": "+254 700 333 444",
                "location": "Mombasa"
            },
            {
                "email": "kisumu.care@gmail.com",
                "password": "password123",
                "name": "Kisumu Care Center",
                "description": "Community health center dedicated to providing accessible healthcare to all.",
                "contact_email": "contact@kisumucare.co.ke",
                "contact_phone": "+254 700 555 666",
                "location": "Kisumu"
            },
            {
                "email": "eldoret.medical@gmail.com",
                "password": "password123",
                "name": "Eldoret Medical Services",
                "description": "Specialized medical facility with state-of-the-art equipment and skilled staff.",
                "contact_email": "info@eldoretmedical.co.ke",
                "contact_phone": "+254 700 777 888",
                "location": "Eldoret"
            },
            {
                "email": "thika.nursing@gmail.com",
                "password": "password123",
                "name": "Thika Nursing Home",
                "description": "Elderly care facility providing compassionate nursing and rehabilitation services.",
                "contact_email": "admin@thikanursing.co.ke",
                "contact_phone": "+254 700 999 000",
                "location": "Thika"
            }
        ]
        
        institution_users = []
        for inst_data in institutions_data:
            user = User(
                email=inst_data["email"],
                password=hash_password(inst_data["password"]),
                role=UserRole.INSTITUTION,
                is_active=True
            )
            db.add(user)
            db.flush()
            
            institution = Institution(
                user_id=user.id,
                institution_name=inst_data["name"],
                description=inst_data["description"],
                contact_email=inst_data["contact_email"],
                contact_phone=inst_data["contact_phone"],
                location=inst_data["location"]
            )
            db.add(institution)
            institution_users.append((user, institution))
        
        db.commit()
        print(f"✅ Created {len(institution_users)} institution users")
        
        # Create Gigs/Jobs
        print("Creating gigs...")
        gigs_data = [
            {
                "title": "Urgent: Night Shift Nurse Needed",
                "description": "We need an experienced registered nurse for night shift coverage (8 PM - 6 AM). Patient care in general ward. Must have valid nursing license.",
                "location": "Nairobi CBD",
                "pay_amount": 8000,
                "duration_hours": 10,
                "is_urgent": True,
                "status": JobStatus.OPEN
            },
            {
                "title": "General Practitioner for Weekend Clinic",
                "description": "Looking for a GP to cover weekend clinic hours. Handle consultations, prescriptions, and minor procedures. Saturday and Sunday 9 AM - 5 PM.",
                "location": "Mombasa",
                "pay_amount": 25000,
                "duration_hours": 16,
                "is_urgent": False,
                "status": JobStatus.OPEN
            },
            {
                "title": "Elderly Care Assistant Required",
                "description": "Need a compassionate caregiver for elderly patient. Duties include medication management, mobility assistance, and companionship. 12-hour shifts.",
                "location": "Kisumu",
                "pay_amount": 6000,
                "duration_hours": 12,
                "is_urgent": False,
                "status": JobStatus.OPEN
            },
            {
                "title": "Emergency Paramedic - Standby Service",
                "description": "Paramedic needed for event standby service. Must be certified in emergency response and first aid. Equipment provided.",
                "location": "Nakuru",
                "pay_amount": 10000,
                "duration_hours": 8,
                "is_urgent": True,
                "status": JobStatus.ASSIGNED
            },
            {
                "title": "Physical Therapist for Rehabilitation",
                "description": "Seeking licensed physical therapist for post-surgery rehabilitation sessions. 3 sessions per week, 2 hours each.",
                "location": "Nairobi",
                "pay_amount": 15000,
                "duration_hours": 6,
                "is_urgent": False,
                "status": JobStatus.OPEN
            },
            {
                "title": "ICU Nurse - 24 Hour Coverage",
                "description": "Experienced ICU nurse needed for critical patient care. Must be comfortable with ventilators and monitoring equipment.",
                "location": "Eldoret",
                "pay_amount": 12000,
                "duration_hours": 24,
                "is_urgent": True,
                "status": JobStatus.OPEN
            },
            {
                "title": "Home Nursing Care for Recovery Patient",
                "description": "Post-operative care needed for patient recovering at home. Wound care, medication, and vitals monitoring.",
                "location": "Thika",
                "pay_amount": 7000,
                "duration_hours": 8,
                "is_urgent": False,
                "status": JobStatus.COMPLETED
            },
            {
                "title": "Medical Consultation Services",
                "description": "Doctor needed for medical consultations at corporate wellness event. Provide health screenings and advice.",
                "location": "Nairobi",
                "pay_amount": 18000,
                "duration_hours": 6,
                "is_urgent": False,
                "status": JobStatus.OPEN
            },
            {
                "title": "Pediatric Nurse for Children's Ward",
                "description": "Pediatric nurse needed for children's ward coverage. Experience with children essential. Day shift 7 AM - 7 PM.",
                "location": "Mombasa",
                "pay_amount": 9000,
                "duration_hours": 12,
                "is_urgent": False,
                "status": JobStatus.OPEN
            },
            {
                "title": "Physiotherapy Session - Sports Injury",
                "description": "Need physiotherapist for sports injury rehabilitation. Focus on knee recovery and strength building.",
                "location": "Kisumu",
                "pay_amount": 5000,
                "duration_hours": 2,
                "is_urgent": False,
                "status": JobStatus.COMPLETED
            }
        ]
        
        jobs = []
        for i, gig_data in enumerate(gigs_data):
            institution = institution_users[i % len(institution_users)][1]
            
            job = Job(
                institution_id=institution.id,
                title=gig_data["title"],
                description=gig_data["description"],
                location=gig_data["location"],
                pay_amount=gig_data["pay_amount"],
                duration_hours=gig_data["duration_hours"],
                is_urgent=gig_data["is_urgent"],
                status=gig_data["status"],
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            
            # Assign some gigs to professionals
            if gig_data["status"] in [JobStatus.ASSIGNED, JobStatus.COMPLETED]:
                professional = professional_users[i % len(professional_users)][1]
                job.assigned_professional_id = professional.id
            
            db.add(job)
            jobs.append(job)
        
        db.commit()
        print(f"✅ Created {len(jobs)} gigs")
        
        # Create Gig Interests
        print("Creating gig interests...")
        interests_created = 0
        for job in jobs:
            if job.status == JobStatus.OPEN:
                # Random 1-3 professionals express interest
                num_interests = random.randint(1, 3)
                interested_profs = random.sample(professional_users, min(num_interests, len(professional_users)))
                
                for user, professional in interested_profs:
                    interest = GigInterest(
                        job_id=job.id,
                        professional_id=professional.id,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5))
                    )
                    db.add(interest)
                    interests_created += 1
        
        db.commit()
        print(f"✅ Created {interests_created} gig interests")
        
        # Create Payments for completed/assigned gigs
        print("Creating payments...")
        payments_created = 0
        for job in jobs:
            if job.status in [JobStatus.ASSIGNED, JobStatus.COMPLETED] and job.assigned_professional_id:
                payment = Payment(
                    gig_id=job.id,
                    institution_id=job.institution_id,
                    professional_id=job.assigned_professional_id,
                    amount=job.pay_amount,
                    pesapal_merchant_reference=f"QGIG-{job.id}-{random.randint(1000, 9999)}",
                    pesapal_order_tracking_id=f"ORDER-{random.randint(100000, 999999)}" if job.status == JobStatus.COMPLETED else None,
                    status=TransactionStatus.COMPLETED if job.status == JobStatus.COMPLETED else TransactionStatus.PENDING,
                    payment_method="M-Pesa" if random.random() > 0.5 else "Card",
                    created_at=job.created_at + timedelta(hours=2),
                    completed_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)) if job.status == JobStatus.COMPLETED else None
                )
                db.add(payment)
                payments_created += 1
        
        db.commit()
        print(f"✅ Created {payments_created} payments")
        
        # Create Ratings for completed gigs
        print("Creating ratings...")
        ratings_created = 0
        for job in jobs:
            if job.status == JobStatus.COMPLETED and job.assigned_professional_id:
                # Institution rates professional
                rating1 = Rating(
                    gig_id=job.id,
                    rater_id=job.institution.user_id,
                    rated_id=job.assigned_professional.user_id,
                    rating=random.uniform(4.0, 5.0),
                    review=random.choice([
                        "Excellent work! Very professional and skilled.",
                        "Great service, highly recommend!",
                        "Professional and punctual. Will hire again.",
                        "Outstanding performance, exceeded expectations.",
                        "Reliable and competent. Thank you!"
                    ]),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15))
                )
                db.add(rating1)
                ratings_created += 1
                
                # Professional rates institution
                rating2 = Rating(
                    gig_id=job.id,
                    rater_id=job.assigned_professional.user_id,
                    rated_id=job.institution.user_id,
                    rating=random.uniform(4.0, 5.0),
                    review=random.choice([
                        "Great facility to work with. Well organized.",
                        "Professional environment and supportive staff.",
                        "Smooth experience, payment on time.",
                        "Would definitely work with them again.",
                        "Excellent communication and clear expectations."
                    ]),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15))
                )
                db.add(rating2)
                ratings_created += 1
        
        db.commit()
        print(f"✅ Created {ratings_created} ratings")
        
        # Create some sample documents
        print("Creating sample documents...")
        documents_created = 0
        for user, professional in professional_users[:3]:
            # Add a verified document
            doc = Document(
                user_id=user.id,
                document_type="certificate",
                file_path=f"uploads/documents/{user.id}_certificate_sample.pdf",
                file_name="nursing_certificate.pdf",
                status=DocumentStatus.APPROVED,
                uploaded_at=datetime.utcnow() - timedelta(days=random.randint(10, 60)),
                reviewed_at=datetime.utcnow() - timedelta(days=random.randint(1, 9)),
                reviewed_by=admin_user.id
            )
            db.add(doc)
            documents_created += 1
        
        db.commit()
        print(f"✅ Created {documents_created} documents")
        
        # Create job interests and notifications
        print("Creating job interests and notifications...")
        try:
            # Clear existing interests and notifications
            db.query(JobInterest).delete()
            db.query(Notification).delete()
            db.commit()
            
            job_interests = []
            num_interests = 20
            
            for i in range(num_interests):
                _, professional = random.choice(professional_users)
                job = random.choice([j for j in jobs if j.status == JobStatus.OPEN])
                
                # Check if interest already exists
                existing = db.query(JobInterest).filter(
                    JobInterest.job_id == job.id,
                    JobInterest.professional_id == professional.id
                ).first()
                
                if existing:
                    continue
                
                # Random status distribution
                status_choice = random.choices(
                    [InterestStatus.PENDING, InterestStatus.ACCEPTED, InterestStatus.DECLINED],
                    weights=[0.5, 0.3, 0.2]
                )[0]
                
                interest = JobInterest(
                    job_id=job.id,
                    professional_id=professional.id,
                    status=status_choice,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15))
                )
                db.add(interest)
                db.flush()
                job_interests.append(interest)
                
                # Create notification for institution
                institution_user = db.query(User).filter(User.id == job.institution.user_id).first()
                notif = Notification(
                    user_id=institution_user.id,
                    title="New Interest in Your Gig",
                    message=f"A professional has shown interest in your gig: {job.title}.",
                    is_read=random.choice([True, False]),
                    job_interest_id=interest.id,
                    created_at=interest.created_at
                )
                db.add(notif)
                
                # If accepted or declined, create notification for professional
                if status_choice in [InterestStatus.ACCEPTED, InterestStatus.DECLINED]:
                    prof_user = db.query(User).filter(User.id == professional.user_id).first()
                    status_text = "ACCEPTED" if status_choice == InterestStatus.ACCEPTED else "DECLINED"
                    prof_notif = Notification(
                        user_id=prof_user.id,
                        title=f"Interest {status_text}",
                        message=f"Your interest in the gig '{job.title}' has been {status_text}.",
                        is_read=random.choice([True, False]),
                        created_at=interest.created_at + timedelta(hours=random.randint(1, 24))
                    )
                    db.add(prof_notif)
            
            db.commit()
            print(f"✅ Created {len(job_interests)} job interests with notifications")
        except Exception as e:
            print(f"❌ Error creating job interests: {str(e)}")
            db.rollback()
            raise
        
        print("="*50)
        print("🎉 Database seeding completed successfully!")
        print("="*50)
        print()
        print("📊 Summary:")
        print(f"   - Admin users: 1")
        print(f"   - Professional users: {len(professional_users)}")
        print(f"   - Institution users: {len(institution_users)}")
        print(f"   - Total gigs: {len(jobs)}")
        print(f"   - Gig interests: {interests_created}")
        print(f"   - Payments: {payments_created}")
        print(f"   - Ratings: {ratings_created}")
        print(f"   - Documents: {documents_created}")
        print(f"   - Job interests: 20")
        print(f"   - Notifications: created")
        print()
        print("🔑 Login Credentials:")
        print(f"   Admin: admin@qgig.com / admin123")
        print(f"   Professional: sarah.nurse@gmail.com / password123")
        print(f"   Institution: nairobi.hospital@gmail.com / password123")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Seed the database
    seed_database()
