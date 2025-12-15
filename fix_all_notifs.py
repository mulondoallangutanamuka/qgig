"""Fix ALL notifications to have proper job_interest_id"""
from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest
from app.models.job import Job
from app.models.professional import Professional
import re

db = SessionLocal()

print("="*80)
print("FIXING ALL NOTIFICATIONS")
print("="*80)

# Get all notifications
all_notifs = db.query(Notification).all()
print(f"\nTotal notifications: {len(all_notifs)}")

# Get all job interests
all_interests = db.query(JobInterest).all()
print(f"Total job interests: {len(all_interests)}")

fixed = 0
for notif in all_notifs:
    if notif.job_interest_id is not None:
        print(f"  Notification {notif.id}: Already has job_interest_id={notif.job_interest_id}")
        continue
    
    # Try to extract job title from message
    # Message format: "{professional_name} has expressed interest in your job: {job_title}"
    if "has expressed interest in your job:" in notif.message:
        # Extract job title
        job_title = notif.message.split("has expressed interest in your job:")[-1].strip()
        
        # Find matching job
        job = db.query(Job).filter(Job.title == job_title).first()
        if not job:
            print(f"  Notification {notif.id}: Could not find job '{job_title}'")
            continue
        
        # Find job interest for this job and user
        # We need to find which professional expressed interest
        # Extract professional name from message
        prof_name = notif.message.split(" has expressed interest")[0].strip()
        
        # Find professional by name
        professional = db.query(Professional).filter(Professional.full_name == prof_name).first()
        if not professional:
            print(f"  Notification {notif.id}: Could not find professional '{prof_name}'")
            continue
        
        # Find the job interest
        interest = db.query(JobInterest).filter(
            JobInterest.job_id == job.id,
            JobInterest.professional_id == professional.id
        ).first()
        
        if interest:
            notif.job_interest_id = interest.id
            print(f"  ✓ Fixed notification {notif.id}: Set job_interest_id={interest.id}")
            fixed += 1
        else:
            print(f"  Notification {notif.id}: Could not find matching interest")
    else:
        print(f"  Notification {notif.id}: Not a job interest notification")

db.commit()

print(f"\n✓ Fixed {fixed} notifications")
print("="*80)

# Verify
print("\nVerification:")
all_notifs = db.query(Notification).all()
for n in all_notifs:
    status = "✓ HAS job_interest_id" if n.job_interest_id else "✗ MISSING job_interest_id"
    print(f"  Notification {n.id}: {status}")

db.close()
