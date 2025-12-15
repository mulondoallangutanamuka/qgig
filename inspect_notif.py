from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest

db = SessionLocal()

notif = db.query(Notification).filter(Notification.id == 1).first()
print(f"Notification ID: {notif.id}")
print(f"Title: {notif.title}")
print(f"Message: {notif.message}")
print(f"User ID: {notif.user_id}")
print(f"job_interest_id: {notif.job_interest_id}")
print()

print("Available job interests:")
interests = db.query(JobInterest).all()
for i in interests:
    print(f"  Interest {i.id}: job_id={i.job_id}, professional_id={i.professional_id}, status={i.status.value}")

db.close()
