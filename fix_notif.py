import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest
from app.models.job import Job

db = SessionLocal()

# Get all job interests
interests = db.query(JobInterest).all()
print(f"Total job interests: {len(interests)}")

if interests:
    # Use the first pending interest
    interest = interests[0]
    print(f"\nUsing Interest ID: {interest.id}")
    print(f"  Job ID: {interest.job_id}")
    print(f"  Professional ID: {interest.professional_id}")
    print(f"  Status: {interest.status.value}")
    
    # Get the job
    job = db.query(Job).filter(Job.id == interest.job_id).first()
    if job:
        print(f"  Job Title: {job.title}")
        print(f"  Institution ID: {job.institution_id}")
        
        # Find notification for this institution
        from app.models.institution import Institution
        institution = db.query(Institution).filter(Institution.id == job.institution_id).first()
        if institution:
            print(f"  Institution User ID: {institution.user_id}")
            
            # Update the notification
            notif = db.query(Notification).filter(
                Notification.user_id == institution.user_id,
                Notification.job_interest_id == None
            ).first()
            
            if notif:
                print(f"\nUpdating Notification ID: {notif.id}")
                notif.job_interest_id = interest.id
                db.commit()
                print("✓ FIXED!")
            else:
                print("\nNo broken notification found")

db.close()
