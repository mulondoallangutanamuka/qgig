"""
Test script for real-time notification system
Run this after starting the Flask server
"""
import requests
import time

BASE_URL = "http://localhost:5000"

def test_notification_system():
    """Test the complete notification workflow"""
    
    print("=" * 60)
    print("Real-Time Notification System - Test Script")
    print("=" * 60)
    
    session_professional = requests.Session()
    session_institution = requests.Session()
    
    # Step 1: Create test accounts
    print("\n[1/8] Creating test accounts...")
    
    # Register professional
    try:
        resp = session_professional.post(f"{BASE_URL}/signup", data={
            'email': f'testpro_{int(time.time())}@test.com',
            'password': 'test123',
            'confirm_password': 'test123',
            'role': 'professional'
        }, allow_redirects=False)
        print(f"   ✓ Professional account created")
    except Exception as e:
        print(f"   ✗ Error creating professional: {e}")
        return
    
    # Register institution
    try:
        resp = session_institution.post(f"{BASE_URL}/signup", data={
            'email': f'testinst_{int(time.time())}@test.com',
            'password': 'test123',
            'confirm_password': 'test123',
            'role': 'institution'
        }, allow_redirects=False)
        print(f"   ✓ Institution account created")
    except Exception as e:
        print(f"   ✗ Error creating institution: {e}")
        return
    
    # Step 2: Login professional
    print("\n[2/8] Logging in as professional...")
    resp = session_professional.post(f"{BASE_URL}/login", data={
        'email': f'testpro_{int(time.time())}@test.com',
        'password': 'test123'
    }, allow_redirects=False)
    
    if resp.status_code in [200, 302]:
        print("   ✓ Professional logged in")
    else:
        print(f"   ✗ Professional login failed: {resp.status_code}")
    
    # Step 3: Login institution
    print("\n[3/8] Logging in as institution...")
    resp = session_institution.post(f"{BASE_URL}/login", data={
        'email': f'testinst_{int(time.time())}@test.com',
        'password': 'test123'
    }, allow_redirects=False)
    
    if resp.status_code in [200, 302]:
        print("   ✓ Institution logged in")
    else:
        print(f"   ✗ Institution login failed: {resp.status_code}")
    
    # Step 4: Update institution profile
    print("\n[4/8] Setting up institution profile...")
    resp = session_institution.post(f"{BASE_URL}/profile/update", data={
        'name': 'Test Institution',
        'description': 'Test description',
        'contact_email': 'test@institution.com',
        'location': 'Nairobi'
    })
    print("   ✓ Institution profile updated")
    
    # Step 5: Post a job
    print("\n[5/8] Posting a test job...")
    resp = session_institution.post(f"{BASE_URL}/gigs/post", data={
        'title': 'Test Web Developer Job',
        'description': 'This is a test job for notification testing',
        'location': 'Nairobi',
        'pay_amount': '50000',
        'duration_hours': '40',
        'is_urgent': 'on'
    }, allow_redirects=False)
    
    if resp.status_code in [200, 302]:
        print("   ✓ Job posted successfully")
    else:
        print(f"   ✗ Job posting failed: {resp.status_code}")
    
    # Step 6: Get job ID
    print("\n[6/8] Fetching job details...")
    resp = session_professional.get(f"{BASE_URL}/gigs")
    if 'Test Web Developer Job' in resp.text:
        print("   ✓ Job is visible to professionals")
        # Extract job ID from page (simple extraction)
        import re
        match = re.search(r'/gigs/(\d+)', resp.text)
        if match:
            job_id = match.group(1)
            print(f"   ✓ Job ID: {job_id}")
        else:
            print("   ✗ Could not find job ID")
            return
    else:
        print("   ✗ Job not found in listings")
        return
    
    # Step 7: Update professional profile
    print("\n[7/8] Setting up professional profile...")
    resp = session_professional.post(f"{BASE_URL}/profile/update", data={
        'name': 'Test Professional',
        'skills': 'Python, Flask, JavaScript',
        'bio': 'Test bio',
        'location': 'Nairobi',
        'hourly_rate': '1000'
    })
    print("   ✓ Professional profile updated")
    
    # Step 8: Express interest (triggers notification)
    print("\n[8/8] Professional expressing interest...")
    print("   → This should trigger a REAL-TIME notification to the institution")
    
    resp = session_professional.post(f"{BASE_URL}/jobs/{job_id}/interest", 
                                     headers={'Content-Type': 'application/json'})
    
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            print("   ✓ Interest expressed successfully!")
            print(f"   ✓ Interest ID: {data.get('interest_id')}")
            print("\n" + "=" * 60)
            print("SUCCESS! Check the institution's browser for:")
            print("  1. Toast notification appearing in top-right")
            print("  2. Notification badge updating (+1)")
            print("  3. Browser console showing socket event")
            print("=" * 60)
        else:
            print(f"   ✗ Interest failed: {data}")
    else:
        print(f"   ✗ Interest request failed: {resp.status_code}")
        print(f"   Response: {resp.text}")
    
    print("\n[NEXT STEPS]")
    print("1. Open browser and login as institution")
    print("2. Navigate to Notifications page")
    print("3. You should see the interest notification with Accept/Reject buttons")
    print("4. Click Accept or Reject to test the response notification")
    print("5. Professional should receive real-time notification of the decision")
    
    print("\n[TEST COMPLETE]")

if __name__ == "__main__":
    try:
        # Check if server is running
        resp = requests.get(BASE_URL, timeout=2)
        print("✓ Server is running\n")
        test_notification_system()
    except requests.exceptions.ConnectionError:
        print("✗ Error: Server is not running!")
        print("Please start the server with: python main.py")
    except Exception as e:
        print(f"✗ Error: {e}")

