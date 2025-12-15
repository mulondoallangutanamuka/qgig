from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest

db = SessionLocal()

# Get the notification from the screenshot
notif = db.query(Notification).filter(Notification.title.like('%New Interest%')).first()

if notif:
    print(f"Notification ID: {notif.id}")
    print(f"Title: {notif.title}")
    print(f"Message: {notif.message}")
    print(f"Job Interest ID: {notif.job_interest_id}")
    print(f"User ID: {notif.user_id}")
    
    if notif.job_interest_id:
        interest = db.query(JobInterest).filter(JobInterest.id == notif.job_interest_id).first()
        if interest:
            print(f"\nJob Interest Found:")
            print(f"  Interest ID: {interest.id}")
            print(f"  Status: {interest.status.value}")
            print(f"  Job ID: {interest.job_id}")
            print(f"  Professional ID: {interest.professional_id}")
        else:
            print("\nJob Interest NOT FOUND in database!")
    else:
        print("\nNo job_interest_id on notification!")
else:
    print("No notification found!")
    
    # Show all notifications
    all_notifs = db.query(Notification).all()
    print(f"\nTotal notifications: {len(all_notifs)}")
    for n in all_notifs[:5]:
        print(f"  - ID {n.id}: {n.title} (job_interest_id: {n.job_interest_id})")

db.close()
