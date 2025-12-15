"""
Comprehensive test script for all application routes
"""
import sys
sys.path.insert(0, '.')

from app import create_app
from app.database import SessionLocal
from app.models.user import User
from app.models.job import Job

print("="*60)
print("TESTING ALL APPLICATION ROUTES")
print("="*60)

# Create app
app, socketio = create_app()

# Test database connectivity
print("\n[1] Testing Database Connectivity...")
try:
    db = SessionLocal()
    user_count = db.query(User).count()
    job_count = db.query(Job).count()
    print(f"✓ Database connected")
    print(f"  - Users: {user_count}")
    print(f"  - Jobs: {job_count}")
    db.close()
except Exception as e:
    print(f"✗ Database error: {e}")

# Test routes
print("\n[2] Testing Routes...")
with app.test_client() as client:
    routes_to_test = [
        ('/', 'Home'),
        ('/login', 'Login'),
        ('/signup', 'Signup'),
        ('/browse_gigs', 'Browse Gigs'),
    ]
    
    for route, name in routes_to_test:
        try:
            response = client.get(route)
            status = "✓" if response.status_code in [200, 302] else "✗"
            print(f"{status} {name} ({route}): {response.status_code}")
        except Exception as e:
            print(f"✗ {name} ({route}): ERROR - {str(e)[:50]}")

# Test authentication
print("\n[3] Testing Authentication...")
with app.test_client() as client:
    try:
        # Test login
        response = client.post('/login', data={
            'email': 'nairobi.hospital@gmail.com',
            'password': 'password123'
        }, follow_redirects=False)
        
        if response.status_code in [200, 302]:
            print(f"✓ Login endpoint working: {response.status_code}")
        else:
            print(f"✗ Login failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Login error: {e}")

# Test protected routes
print("\n[4] Testing Protected Routes...")
with app.test_client() as client:
    # Login first
    client.post('/login', data={
        'email': 'nairobi.hospital@gmail.com',
        'password': 'password123'
    })
    
    protected_routes = [
        ('/my_gigs', 'My Gigs'),
        ('/notifications', 'Notifications'),
        ('/profile', 'Profile'),
    ]
    
    for route, name in protected_routes:
        try:
            response = client.get(route)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {name} ({route}): {response.status_code}")
        except Exception as e:
            print(f"✗ {name} ({route}): ERROR - {str(e)[:50]}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
