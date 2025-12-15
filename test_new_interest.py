"""
Test creating a new interest to verify notifications get job_interest_id automatically
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("="*80)
print("TESTING NEW INTEREST CREATION")
print("="*80)

# Login as professional
print("\n1. Logging in as professional...")
session = requests.Session()
login_response = session.post(f"{BASE_URL}/login", data={
    'email': 'sarah.nurse@gmail.com',
    'password': 'password123'
})

if login_response.status_code == 200:
    print("   ✓ Logged in as sarah.nurse@gmail.com")
else:
    print(f"   ✗ Login failed: {login_response.status_code}")
    exit(1)

# Find an open gig
print("\n2. Finding an open gig...")
gigs_response = session.get(f"{BASE_URL}/api/gigs")
gigs = gigs_response.json()

# Find a gig we haven't expressed interest in yet
available_gig = None
for gig in gigs:
    if gig.get('status') == 'open':
        available_gig = gig
        break

if not available_gig:
    print("   ✗ No open gigs available")
    exit(1)

print(f"   ✓ Found gig: {available_gig['title']} (ID: {available_gig['id']})")

# Express interest
print(f"\n3. Expressing interest in gig {available_gig['id']}...")
interest_response = session.post(f"{BASE_URL}/gigs/{available_gig['id']}/express-interest")

if interest_response.status_code == 200:
    print("   ✓ Interest expressed successfully!")
    result = interest_response.json()
    print(f"   Interest ID: {result.get('interest_id')}")
    print(f"   Notification ID: {result.get('notification_id')}")
else:
    print(f"   ✗ Failed: {interest_response.status_code}")
    print(f"   Response: {interest_response.text}")
    exit(1)

# Verify notification has job_interest_id
print("\n4. Verifying notification has job_interest_id...")
from app.database import SessionLocal
from app.models.notification import Notification

db = SessionLocal()
notification_id = interest_response.json().get('notification_id')
notif = db.query(Notification).filter(Notification.id == notification_id).first()

if notif:
    print(f"   Notification ID: {notif.id}")
    print(f"   job_interest_id: {notif.job_interest_id}")
    
    if notif.job_interest_id:
        print(f"\n   ✅ SUCCESS! Notification has job_interest_id={notif.job_interest_id}")
        print(f"   ✅ Accept/Reject buttons WILL APPEAR for this notification!")
    else:
        print(f"\n   ✗ FAILED! Notification has job_interest_id=None")
        print(f"   ✗ Accept/Reject buttons will NOT appear")
else:
    print(f"   ✗ Notification {notification_id} not found")

db.close()

print("\n" + "="*80)
