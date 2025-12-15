from app.database import SessionLocal
from app.models.notification import Notification
from sqlalchemy import desc

db = SessionLocal()
notifs = db.query(Notification).order_by(desc(Notification.created_at)).limit(10).all()

print("Recent notifications:")
print("="*80)
for n in notifs:
    print(f"ID: {n.id}")
    print(f"  Title: {n.title}")
    print(f"  job_interest_id: {n.job_interest_id}")
    print(f"  Created: {n.created_at}")
    print()

db.close()
