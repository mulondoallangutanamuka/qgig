"""
E2E Test for Payment Flow with Token Authentication
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

class PaymentFlowTester:
    def __init__(self):
        self.institution_token = None
        self.professional_token = None
        self.institution_id = None
        self.professional_id = None
        self.gig_id = None
        self.payment_id = None
        self.tests_passed = 0
        self.tests_failed = 0
    
    def log(self, message, status="INFO"):
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{symbols.get(status, 'ℹ️')} {message}")
    
    def assert_test(self, condition, success_msg, error_msg):
        if condition:
            self.log(success_msg, "SUCCESS")
            self.tests_passed += 1
            return True
        else:
            self.log(error_msg, "ERROR")
            self.tests_failed += 1
            return False
    
    def test_institution_register(self):
        """Test 1: Register institution"""
        self.log("\n=== TEST 1: Register Institution ===")
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_inst_{int(time.time())}@test.com",
            "password": "Test@123",
            "role": "institution"
        })
        
        if self.assert_test(
            response.status_code == 201,
            "Institution registered successfully",
            f"Institution registration failed: {response.status_code} - {response.text}"
        ):
            data = response.json()
            self.institution_email = data['user']['email']
            return True
        return False
    
    def test_professional_register(self):
        """Test 2: Register professional"""
        self.log("\n=== TEST 2: Register Professional ===")
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_prof_{int(time.time())}@test.com",
            "password": "Test@123",
            "role": "professional"
        })
        
        if self.assert_test(
            response.status_code == 201,
            "Professional registered successfully",
            f"Professional registration failed: {response.status_code} - {response.text}"
        ):
            data = response.json()
            self.professional_email = data['user']['email']
            return True
        return False
    
    def test_institution_login(self):
        """Test 3: Login as institution"""
        self.log("\n=== TEST 3: Login as Institution ===")
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.institution_email,
            "password": "Test@123"
        })
        
        if self.assert_test(
            response.status_code == 200,
            "Institution login successful",
            f"Institution login failed: {response.status_code} - {response.text}"
        ):
            data = response.json()
            self.institution_token = data.get("token")
            self.institution_id = data.get("user", {}).get("id")
            
            if self.institution_token:
                self.log(f"Token received: {self.institution_token[:30]}...", "INFO")
                return True
            else:
                self.log("No token in response!", "ERROR")
                return False
        return False
    
    def test_professional_login(self):
        """Test 4: Login as professional"""
        self.log("\n=== TEST 4: Login as Professional ===")
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.professional_email,
            "password": "Test@123"
        })
        
        if self.assert_test(
            response.status_code == 200,
            "Professional login successful",
            f"Professional login failed: {response.status_code} - {response.text}"
        ):
            data = response.json()
            self.professional_token = data.get("token")
            self.professional_id = data.get("user", {}).get("id")
            
            if self.professional_token:
                self.log(f"Token received: {self.professional_token[:30]}...", "INFO")
                return True
            else:
                self.log("No token in response!", "ERROR")
                return False
        return False
    
    def test_token_validation(self):
        """Test 5: Validate tokens work"""
        self.log("\n=== TEST 5: Validate Tokens ===")
        
        # Test institution token
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {self.institution_token}"}
        )
        
        if not self.assert_test(
            response.status_code == 200,
            "Institution token validated successfully",
            f"Institution token validation failed: {response.status_code} - {response.text}"
        ):
            return False
        
        # Test professional token
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {self.professional_token}"}
        )
        
        return self.assert_test(
            response.status_code == 200,
            "Professional token validated successfully",
            f"Professional token validation failed: {response.status_code} - {response.text}"
        )
    
    def test_create_profiles(self):
        """Test 6: Create institution and professional profiles"""
        self.log("\n=== TEST 6: Create Profiles ===")
        
        # Create institution profile
        response = requests.post(
            f"{BASE_URL}/api/institution/profile",
            headers={"Authorization": f"Bearer {self.institution_token}"},
            json={
                "institution_name": "Test Institution",
                "description": "Test description",
                "contact_email": self.institution_email,
                "contact_phone": "0700000000",
                "location": "Nairobi"
            }
        )
        
        if not self.assert_test(
            response.status_code == 201,
            "Institution profile created",
            f"Institution profile creation failed: {response.status_code} - {response.text}"
        ):
            return False
        
        # Create professional profile
        response = requests.post(
            f"{BASE_URL}/api/professional/profile",
            headers={"Authorization": f"Bearer {self.professional_token}"},
            json={
                "full_name": "Test Professional",
                "skills": "Testing, Development",
                "hourly_rate": 5000.0
            }
        )
        
        return self.assert_test(
            response.status_code == 201,
            "Professional profile created",
            f"Professional profile creation failed: {response.status_code} - {response.text}"
        )
    
    def test_post_gig(self):
        """Test 7: Post a gig"""
        self.log("\n=== TEST 7: Post Gig ===")
        
        response = requests.post(
            f"{BASE_URL}/api/jobs",
            headers={"Authorization": f"Bearer {self.institution_token}"},
            json={
                "title": "Test Payment Gig",
                "description": "Testing payment flow",
                "location": "Nairobi",
                "pay_amount": 5000.0,
                "duration_hours": 2
            }
        )
        
        if self.assert_test(
            response.status_code == 201,
            "Gig posted successfully",
            f"Gig posting failed: {response.status_code} - {response.text}"
        ):
            data = response.json()
            self.gig_id = data.get("id")
            self.log(f"Gig ID: {self.gig_id}", "INFO")
            return True
        return False
    
    def test_express_interest(self):
        """Test 8: Professional expresses interest"""
        self.log("\n=== TEST 8: Express Interest ===")
        
        response = requests.post(
            f"{BASE_URL}/api/jobs/{self.gig_id}/express-interest",
            headers={"Authorization": f"Bearer {self.professional_token}"}
        )
        
        return self.assert_test(
            response.status_code == 201,
            "Interest expressed successfully",
            f"Express interest failed: {response.status_code} - {response.text}"
        )
    
    def test_accept_interest(self):
        """Test 9: Institution accepts interest"""
        self.log("\n=== TEST 9: Accept Interest ===")
        
        # First get the interest ID
        response = requests.get(
            f"{BASE_URL}/api/jobs/{self.gig_id}/interests",
            headers={"Authorization": f"Bearer {self.institution_token}"}
        )
        
        if response.status_code != 200:
            self.log(f"Failed to get interests: {response.text}", "ERROR")
            return False
        
        interests = response.json()
        if not interests:
            self.log("No interests found", "ERROR")
            return False
        
        interest_id = interests[0]['id']
        
        # Accept the interest
        response = requests.post(
            f"{BASE_URL}/api/jobs/{self.gig_id}/interests/{interest_id}/accept",
            headers={"Authorization": f"Bearer {self.institution_token}"}
        )
        
        return self.assert_test(
            response.status_code == 200,
            "Interest accepted successfully",
            f"Accept interest failed: {response.status_code} - {response.text}"
        )
    
    def test_initiate_payment(self):
        """Test 10: Initiate payment"""
        self.log("\n=== TEST 10: Initiate Payment ===")
        
        response = requests.post(
            f"{BASE_URL}/api/payments/initiate",
            headers={"Authorization": f"Bearer {self.institution_token}"},
            json={"gig_id": self.gig_id}
        )
        
        self.log(f"Payment initiation response: {response.status_code}", "INFO")
        self.log(f"Response body: {response.text}", "INFO")
        
        if self.assert_test(
            response.status_code == 201,
            "Payment initiated successfully",
            f"Payment initiation failed: {response.status_code} - {response.text}"
        ):
            data = response.json()
            self.payment_id = data.get("payment_id")
            self.log(f"Payment ID: {self.payment_id}", "INFO")
            if data.get("redirect_url"):
                self.log(f"PesaPal URL: {data['redirect_url'][:50]}...", "INFO")
            return True
        return False
    
    def test_payment_status(self):
        """Test 11: Check payment status"""
        self.log("\n=== TEST 11: Check Payment Status ===")
        
        if not self.payment_id:
            self.log("No payment ID available", "WARNING")
            return False
        
        response = requests.get(
            f"{BASE_URL}/api/payments/my-payments",
            headers={"Authorization": f"Bearer {self.institution_token}"}
        )
        
        return self.assert_test(
            response.status_code == 200,
            "Payment status retrieved successfully",
            f"Payment status check failed: {response.status_code} - {response.text}"
        )
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("\n" + "="*60)
        self.log("STARTING PAYMENT FLOW E2E TESTS")
        self.log("="*60)
        
        tests = [
            self.test_institution_register,
            self.test_professional_register,
            self.test_institution_login,
            self.test_professional_login,
            self.test_token_validation,
            self.test_create_profiles,
            self.test_post_gig,
            self.test_express_interest,
            self.test_accept_interest,
            self.test_initiate_payment,
            self.test_payment_status
        ]
        
        for test in tests:
            if not test():
                self.log(f"\n⚠️  Test failed, stopping execution", "WARNING")
                break
            time.sleep(0.5)  # Small delay between tests
        
        # Summary
        self.log("\n" + "="*60)
        self.log("TEST SUMMARY")
        self.log("="*60)
        self.log(f"Tests Passed: {self.tests_passed}", "SUCCESS")
        self.log(f"Tests Failed: {self.tests_failed}", "ERROR" if self.tests_failed > 0 else "INFO")
        
        if self.tests_failed == 0:
            self.log("\n🎉 ALL TESTS PASSED! Payment flow is working correctly.", "SUCCESS")
        else:
            self.log(f"\n❌ {self.tests_failed} test(s) failed. Please review the errors above.", "ERROR")
        
        return self.tests_failed == 0

if __name__ == "__main__":
    tester = PaymentFlowTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
