#!/usr/bin/env python
"""Verify all fixes are actually working"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("VERIFICATION TEST - Bug Fixes")
print("="*60)

# Test 1: Import Check
print("\n[TEST 1] Checking imports...")
try:
    from app.routes.web import GigInterest
    print("✓ GigInterest imported successfully from web.py")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

# Test 2: Check respond endpoint exists
print("\n[TEST 2] Checking respond_to_interest endpoint...")
try:
    from app.routes.web import respond_to_interest
    print("✓ respond_to_interest function exists")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

# Test 3: Check database state
print("\n[TEST 3] Checking database state...")
try:
    from app.database import SessionLocal
    from app.models.notification import Notification
    from app.models.job_interest import JobInterest, InterestStatus
    
    db = SessionLocal()
    
    total_notifs = db.query(Notification).count()
    notifs_with_interest = db.query(Notification).filter(Notification.job_interest_id.isnot(None)).count()
    total_interests = db.query(JobInterest).count()
    pending_interests = db.query(JobInterest).filter(JobInterest.status == InterestStatus.PENDING).count()
    
    print(f"  Total notifications: {total_notifs}")
    print(f"  Notifications with job_interest_id: {notifs_with_interest}")
    print(f"  Total job interests: {total_interests}")
    print(f"  Pending interests: {pending_interests}")
    
    if pending_interests == 0:
        print("\n⚠ WARNING: No pending interests found!")
        print("  Accept/Decline buttons will NOT show without pending interests.")
        print("  You need to:")
        print("    1. Login as professional (sarah.nurse@gmail.com)")
        print("    2. Express interest in a gig")
        print("    3. Then login as institution to see buttons")
    
    db.close()
    print("✓ Database accessible")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check Flask routes
print("\n[TEST 4] Checking Flask routes...")
try:
    from app import create_app
    app, socketio = create_app()
    
    with app.app_context():
        respond_route_found = False
        for rule in app.url_map.iter_rules():
            if 'respond' in rule.rule and 'notification' in rule.rule:
                print(f"✓ Found route: {rule.rule} - Methods: {rule.methods}")
                respond_route_found = True
        
        if not respond_route_found:
            print("✗ FAILED: respond route not registered")
            sys.exit(1)
            
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Check template file
print("\n[TEST 5] Checking template updates...")
try:
    template_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', 'notifications.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if '/notifications/${notificationId}/respond' in content:
        print("✓ Template uses new respond endpoint")
    else:
        print("✗ FAILED: Template not updated to use respond endpoint")
        sys.exit(1)
        
    if 'body: JSON.stringify({ action:' in content:
        print("✓ Template sends action in request body")
    else:
        print("✗ FAILED: Template doesn't send action parameter")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("ALL TESTS PASSED ✓")
print("="*60)
print("\nThe code fixes are in place. If buttons still don't show:")
print("1. Make sure you're logged in as INSTITUTION user")
print("2. Make sure there are PENDING interests (see warning above)")
print("3. Check browser console (F12) for JavaScript errors")
print("4. Try clearing browser cache and reload")
