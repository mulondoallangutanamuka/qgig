import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest

db = SessionLocal()

print("=== DATABASE STATE ===")
print(f"Total notifications: {db.query(Notification).count()}")

notifs_with_interest = db.query(Notification).filter(
    Notification.job_interest_id != None
).all()

print(f"Notifications with job_interest_id: {len(notifs_with_interest)}")

for n in notifs_with_interest[:3]:
    print(f"  - Notif {n.id}: job_interest_id={n.job_interest_id}")

interests = db.query(JobInterest).all()
print(f"\nTotal job interests: {len(interests)}")

for i in interests[:5]:
    print(f"  - Interest {i.id}: status={i.status.value}")

db.close()
