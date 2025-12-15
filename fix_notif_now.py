from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest
from app.models.job import Job

db = SessionLocal()

# Get the broken notification
notif = db.query(Notification).filter(Notification.id == 1).first()
print(f"Fixing notification {notif.id}")
print(f"  Current job_interest_id: {notif.job_interest_id}")
print(f"  Message: {notif.message}")

# Find the job "gooo"
job = db.query(Job).filter(Job.title == "gooo").first()
if job:
    print(f"  Found job: {job.title} (ID: {job.id})")
    
    # Find the most recent pending interest for this job
    interest = db.query(JobInterest).filter(
        JobInterest.job_id == job.id
    ).order_by(JobInterest.created_at.desc()).first()
    
    if interest:
        print(f"  Found interest: ID {interest.id}, status={interest.status.value}")
        
        # Update notification
        notif.job_interest_id = interest.id
        db.commit()
        
        print(f"  ✓ Fixed! Set job_interest_id={interest.id}")
    else:
        print("  ✗ No interest found for this job")
else:
    print("  ✗ Job 'gooo' not found")

db.close()
