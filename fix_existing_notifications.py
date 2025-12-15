"""
Script to update existing notifications with job_interest_id
This fixes old notifications so Accept/Decline buttons will appear
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest
from sqlalchemy import and_

db = SessionLocal()

try:
    print("="*60)
    print("Fixing Existing Notifications")
    print("="*60)
    
    # Find all notifications without job_interest_id that mention "interest"
    notifications_without_interest_id = db.query(Notification).filter(
        Notification.job_interest_id == None,
        Notification.message.ilike('%interest%')
    ).all()
    
    print(f"\nFound {len(notifications_without_interest_id)} notifications without job_interest_id")
    
    fixed_count = 0
    
    for notif in notifications_without_interest_id:
        # Try to find matching job interest by parsing the notification message
        # Message format: "Sarah Mwangi has expressed interest in your job: Engineer"
        
        # Get all interests for this institution user
        interests = db.query(JobInterest).join(
            JobInterest.job
        ).filter(
            JobInterest.job.has(institution_id=db.query(Notification).filter(
                Notification.id == notif.id
            ).first().user_id)
        ).all()
        
        # Try to match by timestamp (notifications created around the same time as interests)
        for interest in interests:
            time_diff = abs((notif.created_at - interest.created_at).total_seconds())
            
            # If created within 5 seconds of each other, likely a match
            if time_diff < 5:
                notif.job_interest_id = interest.id
                fixed_count += 1
                print(f"  ✓ Fixed notification {notif.id} → interest {interest.id}")
                break
    
    if fixed_count > 0:
        db.commit()
        print(f"\n✅ Successfully fixed {fixed_count} notifications")
    else:
        print("\n⚠ No notifications could be automatically fixed")
        print("   New interests will have buttons, but old ones won't")
    
    print("\n" + "="*60)
    print("Summary:")
    print(f"  Total notifications checked: {len(notifications_without_interest_id)}")
    print(f"  Notifications fixed: {fixed_count}")
    print(f"  Notifications remaining unfixed: {len(notifications_without_interest_id) - fixed_count}")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

print("\nDone! Refresh the notifications page to see Accept/Decline buttons.")
