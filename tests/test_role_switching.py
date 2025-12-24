import pytest
import requests
import time

BASE_URL = "http://127.0.0.1:5000"


def test_register_creates_multi_role_user():
    """Test that new users get both professional and institution roles"""
    email = f"multirole_{int(time.time())}@test.com"
    
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "email": email,
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "available_roles" in data["user"]
    assert "professional" in data["user"]["available_roles"]
    assert "institution" in data["user"]["available_roles"]


def test_role_switching_success():
    """Test successful role switching"""
    # Register and login
    email = f"roleswitch_{int(time.time())}@test.com"
    
    requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": "testpass123"}
    )
    
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": "testpass123"}
    )
    token = login_response.json()["token"]
    
    # Switch to institution role
    switch_response = requests.post(
        f"{BASE_URL}/api/auth/switch-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "institution"}
    )
    
    assert switch_response.status_code == 200
    data = switch_response.json()
    assert data["active_role"] == "institution"
    assert "token" in data


def test_role_switching_to_unassigned_role_fails():
    """Test that switching to an unassigned role fails"""
    # This test would need a user with only one role assigned
    # For now, all new users get both roles, so this is a placeholder
    pass


def test_cross_role_access_denial():
    """Test that endpoints enforce active_role permissions"""
    # Register and login
    email = f"crossrole_{int(time.time())}@test.com"
    
    requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": "testpass123"}
    )
    
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": "testpass123"}
    )
    token = login_response.json()["token"]
    
    # Default role is professional, try to access institution-only endpoint
    response = requests.post(
        f"{BASE_URL}/api/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Job",
            "description": "Test Description",
            "location": "Test Location",
            "pay_amount": 100
        }
    )
    
    # Should fail because professional role cannot create jobs
    assert response.status_code == 403


def test_role_switching_updates_permissions():
    """Test that switching roles updates access permissions"""
    # Register and login
    email = f"perms_{int(time.time())}@test.com"
    
    requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": "testpass123"}
    )
    
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": "testpass123"}
    )
    token = login_response.json()["token"]
    
    # Switch to institution role
    switch_response = requests.post(
        f"{BASE_URL}/api/auth/switch-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "institution"}
    )
    
    new_token = switch_response.json()["token"]
    
    # Now should be able to create jobs
    response = requests.post(
        f"{BASE_URL}/api/jobs",
        headers={"Authorization": f"Bearer {new_token}"},
        json={
            "title": "Test Job",
            "description": "Test Description",
            "location": "Test Location",
            "pay_amount": 100
        }
    )
    
    # Should succeed now
    assert response.status_code == 201


def test_admin_cannot_switch_roles():
    """Test that admin role cannot be switched to"""
    email = f"admin_switch_{int(time.time())}@test.com"
    
    requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": "testpass123"}
    )
    
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": "testpass123"}
    )
    token = login_response.json()["token"]
    
    # Try to switch to admin
    switch_response = requests.post(
        f"{BASE_URL}/api/auth/switch-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"}
    )
    
    assert switch_response.status_code == 400
    assert "admin" in switch_response.json()["error"].lower()


def test_role_switch_audit_logging():
    """Test that role switches are logged for audit"""
    # This would require database access to verify audit entries
    # Placeholder for future implementation
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
