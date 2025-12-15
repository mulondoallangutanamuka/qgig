import pytest
import requests
import time
import subprocess
import os
import signal
from threading import Thread

BASE_URL = "http://127.0.0.1:5000"

@pytest.fixture(scope="module")
def server():
    """Start Flask server for testing"""
    env = os.environ.copy()
    env["FLASK_ENV"] = "testing"
    
    process = subprocess.Popen(
        ["python", "main.py"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)
    
    yield process
    
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

def test_health_check(server):
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_register_professional(server):
    """Test user registration as professional"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": f"professional_{int(time.time())}@test.com",
            "password": "testpass123",
            "role": "professional"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert data["user"]["role"] == "professional"

def test_register_institution(server):
    """Test user registration as institution"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": f"institution_{int(time.time())}@test.com",
            "password": "testpass123",
            "role": "institution"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["role"] == "institution"

def test_register_missing_fields(server):
    """Test registration with missing fields"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": "test@test.com"}
    )
    assert response.status_code == 400
    assert "error" in response.json()

def test_register_duplicate_email(server):
    """Test registration with duplicate email"""
    email = f"duplicate_{int(time.time())}@test.com"
    
    requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": "pass123", "role": "professional"}
    )
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": "pass123", "role": "professional"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["error"].lower()

def test_register_invalid_role(server):
    """Test registration with invalid role"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": f"invalid_{int(time.time())}@test.com",
            "password": "pass123",
            "role": "invalid_role"
        }
    )
    assert response.status_code == 400

def test_register_admin_forbidden(server):
    """Test that admin role cannot be registered"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": f"admin_{int(time.time())}@test.com",
            "password": "pass123",
            "role": "admin"
        }
    )
    assert response.status_code == 400

def test_login_success(server):
    """Test successful login"""
    email = f"login_{int(time.time())}@test.com"
    password = "testpass123"
    
    requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password, "role": "professional"}
    )
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == email

def test_login_invalid_credentials(server):
    """Test login with invalid credentials"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "nonexistent@test.com", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "error" in response.json()

def test_protected_route_without_token(server):
    """Test accessing protected route without token"""
    response = requests.get(f"{BASE_URL}/auth/me")
    assert response.status_code == 401

def test_protected_route_with_token(server):
    """Test accessing protected route with valid token"""
    email = f"protected_{int(time.time())}@test.com"
    password = "testpass123"
    
    requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password, "role": "professional"}
    )
    
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    token = login_response.json()["token"]
    
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == email

def test_role_based_access_professional(server):
    """Test role-based access for professional"""
    email = f"role_prof_{int(time.time())}@test.com"
    password = "testpass123"
    
    requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password, "role": "professional"}
    )
    
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    token = login_response.json()["token"]
    
    response = requests.get(
        f"{BASE_URL}/auth/professional-only",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    response = requests.get(
        f"{BASE_URL}/auth/institution-only",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_role_based_access_institution(server):
    """Test role-based access for institution"""
    email = f"role_inst_{int(time.time())}@test.com"
    password = "testpass123"
    
    requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password, "role": "institution"}
    )
    
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    token = login_response.json()["token"]
    
    response = requests.get(
        f"{BASE_URL}/auth/institution-only",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    response = requests.get(
        f"{BASE_URL}/auth/professional-only",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_404_error_handler(server):
    """Test 404 error handler"""
    response = requests.get(f"{BASE_URL}/nonexistent-route")
    assert response.status_code == 404
    assert "error" in response.json()
