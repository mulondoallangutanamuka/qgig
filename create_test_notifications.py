"""Create test notifications with proper job_interest_id"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest
from app.models.job import Job
from app.models.institution import Institution

db = SessionLocal()

print("="*80)
print("CREATING TEST NOTIFICATIONS")
print("="*80)

# Get all job interests
interests = db.query(JobInterest).all()
print(f"\nFound {len(interests)} job interests")

for interest in interests:
    # Check if notification already exists
    existing = db.query(Notification).filter(
        Notification.job_interest_id == interest.id
    ).first()
    
    if existing:
        print(f"  Interest {interest.id}: Already has notification")
        continue
    
    # Get job and institution
    job = db.query(Job).filter(Job.id == interest.job_id).first()
    if not job:
        print(f"  Interest {interest.id}: Job not found")
        continue
    
    institution = db.query(Institution).filter(Institution.id == job.institution_id).first()
    if not institution:
        print(f"  Interest {interest.id}: Institution not found")
        continue
    
    # Get professional name
    from app.models.professional import Professional
    professional = db.query(Professional).filter(Professional.id == interest.professional_id).first()
    prof_name = professional.full_name if professional else "A professional"
    
    # Create notification
    notification = Notification(
        user_id=institution.user_id,
        title="New Interest in Your Job",
        message=f"{prof_name} has expressed interest in your job: {job.title}",
        job_interest_id=interest.id,
        is_read=False
    )
    db.add(notification)
    print(f"  ✓ Created notification for interest {interest.id}")

db.commit()

# Verify
total_notifs = db.query(Notification).count()
print(f"\n✓ Total notifications in database: {total_notifs}")

db.close()

print("\n" + "="*80)
print("TEST NOTIFICATIONS CREATED")
print("="*80)
