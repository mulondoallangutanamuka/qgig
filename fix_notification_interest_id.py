"""Fix existing notifications to have proper job_interest_id"""
from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest
from app.models.job import Job
from app.models.professional import Professional

db = SessionLocal()

# Find notifications about interest that don't have job_interest_id
notifications = db.query(Notification).filter(
    Notification.title.like('%Interest%'),
    Notification.job_interest_id == None
).all()

print(f"Found {len(notifications)} notifications without job_interest_id")

for notif in notifications:
    print(f"\nNotification ID {notif.id}: {notif.title}")
    print(f"  Message: {notif.message}")
    
    # Try to find the related job interest
    # Parse professional name and job title from message
    # Message format: "None has expressed interest in your job: Nurse"
    if "expressed interest in your job:" in notif.message:
        parts = notif.message.split("expressed interest in your job:")
        if len(parts) == 2:
            professional_name = parts[0].strip().replace(" has", "")
            job_title = parts[1].strip()
            
            print(f"  Looking for: Professional '{professional_name}', Job '{job_title}'")
            
            # Find the professional
            professional = db.query(Professional).filter(
                Professional.full_name == professional_name
            ).first()
            
            if professional:
                print(f"  Found professional: {professional.full_name} (ID: {professional.id})")
                
                # Find the job
                job = db.query(Job).filter(Job.title == job_title).first()
                
                if job:
                    print(f"  Found job: {job.title} (ID: {job.id})")
                    
                    # Find the interest
                    interest = db.query(JobInterest).filter(
                        JobInterest.job_id == job.id,
                        JobInterest.professional_id == professional.id
                    ).first()
                    
                    if interest:
                        print(f"  Found interest: ID {interest.id}, Status: {interest.status.value}")
                        
                        # Update notification
                        notif.job_interest_id = interest.id
                        print(f"  ✓ Updated notification {notif.id} with job_interest_id = {interest.id}")
                    else:
                        print(f"  ✗ No interest found for this combination")
                else:
                    print(f"  ✗ Job not found")
            else:
                print(f"  ✗ Professional not found")

db.commit()
print("\n✓ Database updated!")

# Verify the fix
notif_check = db.query(Notification).filter(Notification.id == 1).first()
if notif_check:
    print(f"\nVerification - Notification ID 1:")
    print(f"  Title: {notif_check.title}")
    print(f"  Job Interest ID: {notif_check.job_interest_id}")
    if notif_check.job_interest_id:
        print("  ✓ FIXED - Buttons should now appear!")
    else:
        print("  ✗ Still broken")

db.close()
