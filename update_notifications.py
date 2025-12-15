import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest

db = SessionLocal()

print("Updating existing notifications...")

# Get all notifications without job_interest_id
notifs = db.query(Notification).filter(
    Notification.job_interest_id == None,
    Notification.message.contains('interest')
).all()

print(f"Found {len(notifs)} notifications to fix")

fixed = 0
for notif in notifs:
    # Find matching interest by timestamp
    interests = db.query(JobInterest).all()
    for interest in interests:
        time_diff = abs((notif.created_at - interest.created_at).total_seconds())
        if time_diff < 10:
            notif.job_interest_id = interest.id
            fixed += 1
            print(f"Fixed notification {notif.id}")
            break

db.commit()
db.close()

print(f"Fixed {fixed} notifications")
