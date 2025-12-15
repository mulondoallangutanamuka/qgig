"""
Quick test script to verify the fixes are working
"""
import sys
sys.path.insert(0, 'c:/Users/my pc/Desktop/qgig')

from app import create_app
from app.database import SessionLocal
from app.models.notification import Notification
from app.models.job_interest import JobInterest
from sqlalchemy.orm import joinedload

app, socketio = create_app()

with app.app_context():
    db = SessionLocal()
    
    # Test 1: Check if GigInterest is imported in web.py
    print("Test 1: Checking GigInterest import...")
    try:
        from app.routes.web import GigInterest as WebGigInterest
        print("✓ GigInterest is imported in web.py")
    except ImportError as e:
        print(f"✗ GigInterest import failed: {e}")
    
    # Test 2: Check if notifications load job_interest relationship
    print("\nTest 2: Checking notification query...")
    try:
        notifications = db.query(Notification).options(
            joinedload(Notification.job_interest)
        ).limit(5).all()
        
        for notif in notifications:
            if notif.job_interest_id:
                if notif.job_interest:
                    print(f"✓ Notification {notif.id} has job_interest loaded: {notif.job_interest.status}")
                else:
                    print(f"✗ Notification {notif.id} has job_interest_id but job_interest is None")
        
        if not any(n.job_interest_id for n in notifications):
            print("⚠ No notifications with job_interest_id found in database")
            
    except Exception as e:
        print(f"✗ Notification query failed: {e}")
    
    # Test 3: Check if respond_to_interest endpoint exists
    print("\nTest 3: Checking respond_to_interest endpoint...")
    try:
        from app.routes.web import respond_to_interest
        print("✓ respond_to_interest endpoint exists")
    except ImportError as e:
        print(f"✗ respond_to_interest endpoint not found: {e}")
    
    # Test 4: List all routes to verify
    print("\nTest 4: Checking registered routes...")
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            if 'notification' in rule.rule.lower() and 'respond' in rule.rule.lower():
                print(f"✓ Found route: {rule.rule} [{', '.join(rule.methods)}]")
    
    db.close()
    
print("\n" + "="*50)
print("Test complete. Check results above.")
