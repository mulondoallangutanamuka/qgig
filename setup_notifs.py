import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest
from app.models.job import Job
from app.models.institution import Institution
from app.models.professional import Professional

db = SessionLocal()

interests = db.query(JobInterest).all()
print(f'Found {len(interests)} interests')

created = 0
for i in interests:
    existing = db.query(Notification).filter(Notification.job_interest_id == i.id).first()
    if existing:
        continue
    
    job = db.query(Job).filter(Job.id == i.job_id).first()
    if not job:
        continue
    
    inst = db.query(Institution).filter(Institution.id == job.institution_id).first()
    if not inst:
        continue
    
    prof = db.query(Professional).filter(Professional.id == i.professional_id).first()
    prof_name = prof.full_name if prof else "Someone"
    
    notif = Notification(
        user_id=inst.user_id,
        title="New Interest in Your Job",
        message=f"{prof_name} has expressed interest in your job: {job.title}",
        job_interest_id=i.id
    )
    db.add(notif)
    created += 1

db.commit()
print(f'Created {created} notifications')

total = db.query(Notification).count()
print(f'Total notifications: {total}')

db.close()
