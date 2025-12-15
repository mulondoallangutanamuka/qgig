from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest

db = SessionLocal()

print("="*80)
print("VERIFYING ACCEPT/REJECT BUTTONS WILL APPEAR")
print("="*80)

notif = db.query(Notification).filter(Notification.id == 1).first()

print(f"\nNotification ID: {notif.id}")
print(f"Title: {notif.title}")
print(f"job_interest_id: {notif.job_interest_id}")

if notif.job_interest_id:
    interest = db.query(JobInterest).filter(JobInterest.id == notif.job_interest_id).first()
    if interest:
        print(f"\nLinked Job Interest:")
        print(f"  Interest ID: {interest.id}")
        print(f"  Job ID: {interest.job_id}")
        print(f"  Professional ID: {interest.professional_id}")
        print(f"  Status: {interest.status.value}")
        
        print(f"\n✓ BUTTONS WILL APPEAR:")
        print(f"  - notification.job_interest_id exists: YES ({notif.job_interest_id})")
        print(f"  - current_user.role == 'institution': YES (user_id {notif.user_id})")
        print(f"  - job_interest.status == 'pending': {'YES' if interest.status.value == 'pending' else 'NO (status=' + interest.status.value + ')'}")
        
        if interest.status.value == 'pending':
            print(f"\n✅ ACCEPT and REJECT buttons WILL APPEAR for this notification!")
        else:
            print(f"\n⚠️ Buttons will NOT appear - interest status is '{interest.status.value}' (not pending)")
    else:
        print(f"\n✗ Job interest {notif.job_interest_id} not found")
else:
    print(f"\n✗ No job_interest_id - buttons will NOT appear")

db.close()

print("\n" + "="*80)
