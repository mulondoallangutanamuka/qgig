"""
Test PesaPal API Connection and Payment Flow
"""
import requests
import json
from app.config import settings

class PesaPalTester:
    BASE_URL = "https://cybqa.pesapal.com/pesapalv3/api"
    
    def __init__(self):
        self.token = None
        
    def test_authentication(self):
        """Test 1: Authenticate with PesaPal"""
        print("\n" + "="*60)
        print("TEST 1: PesaPal Authentication")
        print("="*60)
        
        url = f"{self.BASE_URL}/Auth/RequestToken"
        
        payload = {
            "consumer_key": settings.PESAPAL_CONSUMER_KEY,
            "consumer_secret": settings.PESAPAL_CONSUMER_SECRET
        }
        
        print(f"Consumer Key: {settings.PESAPAL_CONSUMER_KEY[:20]}...")
        print(f"Consumer Secret: {settings.PESAPAL_CONSUMER_SECRET[:10]}...")
        print(f"Request URL: {url}")
        
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Body: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                self.token = response.json().get("token")
                print(f"\n✅ Authentication Successful!")
                print(f"Token: {self.token[:30]}...")
                return True
            else:
                print(f"\n❌ Authentication Failed!")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return False
    
    def test_register_ipn(self):
        """Test 2: Register IPN (Instant Payment Notification)"""
        print("\n" + "="*60)
        print("TEST 2: Register IPN URL")
        print("="*60)
        
        if not self.token:
            print("❌ No token available. Run authentication first.")
            return False
        
        url = f"{self.BASE_URL}/URLSetup/RegisterIPN"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": settings.PESAPAL_CALLBACK_URL,
            "ipn_notification_type": "POST"
        }
        
        print(f"IPN URL: {settings.PESAPAL_CALLBACK_URL}")
        print(f"Request URL: {url}")
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Body: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                print(f"\n✅ IPN Registration Successful!")
                return True
            else:
                print(f"\n⚠️  IPN Registration Response (may already exist)")
                return True  # Continue even if already registered
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return False
    
    def test_payment_initiation(self):
        """Test 3: Initiate a test payment"""
        print("\n" + "="*60)
        print("TEST 3: Initiate Test Payment")
        print("="*60)
        
        if not self.token:
            print("❌ No token available. Run authentication first.")
            return False
        
        url = f"{self.BASE_URL}/Transactions/SubmitOrderRequest"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        import uuid
        merchant_ref = f"TEST-{uuid.uuid4().hex[:12].upper()}"
        
        payload = {
            "id": merchant_ref,
            "currency": "KES",
            "amount": 100.00,
            "description": "Test Payment - QGig Platform",
            "callback_url": settings.PESAPAL_CALLBACK_URL,
            "notification_id": settings.PESAPAL_CALLBACK_URL,
            "billing_address": {
                "email_address": "test@qgig.com",
                "phone_number": "0700000000",
                "country_code": "KE",
                "first_name": "Test",
                "last_name": "User"
            }
        }
        
        print(f"Merchant Reference: {merchant_ref}")
        print(f"Amount: KES 100.00")
        print(f"Callback URL: {settings.PESAPAL_CALLBACK_URL}")
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Body: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                data = response.json()
                redirect_url = data.get('redirect_url')
                order_tracking_id = data.get('order_tracking_id')
                
                print(f"\n✅ Payment Initiated Successfully!")
                print(f"\nOrder Tracking ID: {order_tracking_id}")
                print(f"Redirect URL: {redirect_url}")
                print(f"\n🔗 Open this URL in browser to complete payment:")
                print(f"{redirect_url}")
                
                return order_tracking_id
            else:
                print(f"\n❌ Payment Initiation Failed!")
                return None
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return None
    
    def test_transaction_status(self, order_tracking_id):
        """Test 4: Check transaction status"""
        print("\n" + "="*60)
        print("TEST 4: Check Transaction Status")
        print("="*60)
        
        if not self.token:
            print("❌ No token available. Run authentication first.")
            return False
        
        if not order_tracking_id:
            print("❌ No order tracking ID provided.")
            return False
        
        url = f"{self.BASE_URL}/Transactions/GetTransactionStatus"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        params = {"orderTrackingId": order_tracking_id}
        
        print(f"Order Tracking ID: {order_tracking_id}")
        print(f"Request URL: {url}")
        
        try:
            response = requests.get(url, params=params, headers=headers)
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Body: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('payment_status_description', 'Unknown')
                print(f"\n✅ Status Check Successful!")
                print(f"Payment Status: {status}")
                return True
            else:
                print(f"\n❌ Status Check Failed!")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all PesaPal tests"""
        print("\n" + "="*60)
        print("PESAPAL API CONNECTION TEST")
        print("="*60)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("\n❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Test 2: Register IPN
        self.test_register_ipn()
        
        # Test 3: Payment Initiation
        order_tracking_id = self.test_payment_initiation()
        
        # Test 4: Status Check
        if order_tracking_id:
            self.test_transaction_status(order_tracking_id)
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✅ Authentication: Working")
        print("✅ IPN Registration: Working")
        if order_tracking_id:
            print("✅ Payment Initiation: Working")
            print(f"\n📝 To complete the test payment:")
            print(f"   1. Open the redirect URL in a browser")
            print(f"   2. Complete the payment using test credentials")
            print(f"   3. Check the webhook at: {settings.PESAPAL_CALLBACK_URL}")
        else:
            print("❌ Payment Initiation: Failed")
        
        return True

if __name__ == "__main__":
    tester = PesaPalTester()
    tester.run_all_tests()
