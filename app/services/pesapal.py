import requests
from app.config import settings
import uuid

class PesaPal:
    BASE_URL = settings.PESAPAL_BASE_URL
    _ipn_id = None

    def get_token(self):
        if not settings.PESAPAL_CONSUMER_KEY or not settings.PESAPAL_CONSUMER_SECRET:
            raise ValueError("Missing PESAPAL_CONSUMER_KEY and/or PESAPAL_CONSUMER_SECRET in environment")

        url = f"{self.BASE_URL}/Auth/RequestToken"

        payload = {
            "consumer_key": settings.PESAPAL_CONSUMER_KEY,
            "consumer_secret": settings.PESAPAL_CONSUMER_SECRET
        }

        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)

            try:
                data = response.json()
            except Exception:
                raise Exception(f"PesaPal token error: non-JSON response (status={response.status_code}): {response.text}")

            if not response.ok:
                raise Exception(f"PesaPal token request failed (status={response.status_code}): {data}")

            token = data.get("token") or data.get("Token") or data.get("access_token")
            if not token:
                raise Exception(f"PesaPal token missing in response (status={response.status_code}): {data}")

            return token
        except Exception as e:
            print(f"PesaPal token error: {e}")
            raise

    def register_ipn(self, token):
        """Register IPN URL and get IPN ID"""
        if not settings.PESAPAL_CALLBACK_URL:
            raise ValueError("Missing PESAPAL_CALLBACK_URL in environment")

        if self._ipn_id:
            return self._ipn_id
            
        url = f"{self.BASE_URL}/URLSetup/RegisterIPN"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": settings.PESAPAL_CALLBACK_URL,
            "ipn_notification_type": "POST"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            self._ipn_id = data.get("ipn_id")
            return self._ipn_id
        except Exception as e:
            print(f"PesaPal IPN registration error: {e}")
            # If IPN already exists, try to get existing IPNs
            return self.get_ipn_list(token)
    
    def get_ipn_list(self, token):
        """Get list of registered IPNs"""
        url = f"{self.BASE_URL}/URLSetup/GetIpnList"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            ipns = response.json()
            
            # Find IPN matching our callback URL
            for ipn in ipns:
                if ipn.get("url") == settings.PESAPAL_CALLBACK_URL:
                    self._ipn_id = ipn.get("ipn_id")
                    return self._ipn_id
            
            # If no match, use first active IPN
            if ipns and len(ipns) > 0:
                self._ipn_id = ipns[0].get("ipn_id")
                return self._ipn_id
                
            return None
        except Exception as e:
            print(f"PesaPal get IPN list error: {e}")
            return None

    def initiate_payment(self, amount, email, phone, merchant_reference=None):
        token = self.get_token()
        
        # Register/Get IPN ID
        ipn_id = self.register_ipn(token)
        if not ipn_id:
            raise Exception("Failed to get IPN ID")

        url = f"{self.BASE_URL}/Transactions/SubmitOrderRequest"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        if not merchant_reference:
            merchant_reference = f"QGIG-{uuid.uuid4().hex[:12].upper()}"

        payload = {
            "id": merchant_reference,
            "currency": "UGX",
            "amount": amount,
            "description": "Qgig Payment",
            "callback_url": settings.PESAPAL_CALLBACK_URL,
            "notification_id": ipn_id,
            "billing_address": {
                "email_address": email,
                "phone_number": phone,
                "country_code": "UG",
                "first_name": "Qgig",
                "last_name": "User"
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            try:
                data = response.json()
            except Exception:
                raise Exception(f"PesaPal payment initiation error: non-JSON response (status={response.status_code}): {response.text}")

            if not response.ok:
                raise Exception(f"PesaPal payment initiation failed (status={response.status_code}): {data}")

            return data
        except Exception as e:
            print(f"PesaPal payment initiation error: {e}")
            print(f"Response: {response.text if 'response' in locals() else 'No response'}")
            raise

    def get_transaction_status(self, order_tracking_id):
        token = self.get_token()

        url = f"{self.BASE_URL}/Transactions/GetTransactionStatus"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {"orderTrackingId": order_tracking_id}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)

            try:
                data = response.json()
            except Exception:
                raise Exception(f"PesaPal status check error: non-JSON response (status={response.status_code}): {response.text}")

            if not response.ok:
                raise Exception(f"PesaPal status check failed (status={response.status_code}): {data}")

            return data
        except Exception as e:
            print(f"PesaPal status check error: {e}")
            raise
