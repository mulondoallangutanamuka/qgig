import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.notification import Notification
from app.models.user import User

db = SessionLocal()

institution_user = db.query(User).filter(User.email == 'nairobi.hospital@gmail.com').first()

if institution_user:
    print(f'Institution user ID: {institution_user.id}')
    print(f'Institution role: {institution_user.role.value}')
    
    notifs = db.query(Notification).filter(Notification.user_id == institution_user.id).all()
    print(f'\nTotal notifications: {len(notifs)}')
    
    for n in notifs:
        print(f'\nNotif {n.id}:')
        print(f'  job_interest_id: {n.job_interest_id}')
        print(f'  title: {n.title}')
        print(f'  message: {n.message[:50]}...')
else:
    print('Institution user not found')

db.close()
