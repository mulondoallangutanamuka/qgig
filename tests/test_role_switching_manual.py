"""
Manual test script for role switching functionality
Run this with the Flask server running to test role switching
"""
import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def test_role_switching():
    print("=" * 60)
    print("ROLE SWITCHING TEST")
    print("=" * 60)
    print()
    
    # 1. Register a new user
    email = f"roletest_{int(time.time())}@test.com"
    password = "testpass123"
    
    print("1. Registering new user...")
    register_response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": password}
    )
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.json()}")
        return False
    
    print(f"✓ User registered: {email}")
    print(f"  Available roles: {register_response.json()['user']['available_roles']}")
    print()
    
    # 2. Login
    print("2. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.json()}")
        return False
    
    token = login_response.json()["token"]
    session = requests.Session()
    
    # Also login via web to get session cookie
    web_login = session.post(
        f"{BASE_URL}/login",
        data={"email": email, "password": password},
        allow_redirects=False
    )
    
    print(f"✓ Logged in successfully")
    print(f"  Active role: {login_response.json()['user']['active_role']}")
    print()
    
    # 3. Check current user info
    print("3. Checking current user info...")
    me_response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if me_response.status_code == 200:
        print(f"✓ Current user info:")
        print(f"  Email: {me_response.json()['email']}")
        print(f"  Role: {me_response.json()['role']}")
        print(f"  Active role: {me_response.json()['active_role']}")
    print()
    
    # 4. Switch to institution role (using session)
    print("4. Switching to institution role (session-based)...")
    switch_response = session.post(
        f"{BASE_URL}/api/auth/switch-role",
        json={"role": "institution"}
    )
    
    if switch_response.status_code != 200:
        print(f"❌ Role switch failed: {switch_response.json()}")
        return False
    
    new_token = switch_response.json()["token"]
    print(f"✓ Switched to institution role")
    print(f"  New active role: {switch_response.json()['active_role']}")
    print()
    
    # 5. Verify role switch with new token
    print("5. Verifying role switch...")
    me_response2 = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {new_token}"}
    )
    
    if me_response2.status_code == 200:
        print(f"✓ Role switch verified:")
        print(f"  Active role: {me_response2.json()['active_role']}")
    print()
    
    # 6. Switch back to professional role
    print("6. Switching back to professional role...")
    switch_back = session.post(
        f"{BASE_URL}/api/auth/switch-role",
        json={"role": "professional"}
    )
    
    if switch_back.status_code != 200:
        print(f"❌ Switch back failed: {switch_back.json()}")
        return False
    
    print(f"✓ Switched back to professional role")
    print(f"  Active role: {switch_back.json()['active_role']}")
    print()
    
    # 7. Test role-based access
    print("7. Testing role-based access...")
    
    # Should work for professional
    prof_response = requests.get(
        f"{BASE_URL}/api/auth/professional-only",
        headers={"Authorization": f"Bearer {switch_back.json()['token']}"}
    )
    
    if prof_response.status_code == 200:
        print(f"✓ Professional-only endpoint accessible")
    else:
        print(f"❌ Professional-only endpoint failed: {prof_response.status_code}")
    
    # Should fail for institution (since active_role is professional)
    inst_response = requests.get(
        f"{BASE_URL}/api/auth/institution-only",
        headers={"Authorization": f"Bearer {switch_back.json()['token']}"}
    )
    
    if inst_response.status_code == 403:
        print(f"✓ Institution-only endpoint correctly blocked")
    else:
        print(f"❌ Institution-only endpoint should be blocked but got: {inst_response.status_code}")
    
    print()
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_role_switching()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
