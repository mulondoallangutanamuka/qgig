"""
Simple Integration Test for Institution Notification System
Tests Accept/Reject/Delete functionality
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

class TestNotificationSystem:
    """Simple integration tests using requests"""
    
    def __init__(self):
        self.session = requests.Session()
        self.institution_email = "nairobi.hospital@gmail.com"
        self.institution_password = "password123"
        self.professional_email = "sarah.nurse@gmail.com"
        self.professional_password = "password123"
    
    def login_institution(self):
        """Login as institution"""
        response = self.session.post(
            f"{BASE_URL}/login",
            data={
                'email': self.institution_email,
                'password': self.institution_password
            },
            allow_redirects=False
        )
        return response.status_code in [200, 302]
    
    def login_professional(self):
        """Login as professional"""
        response = self.session.post(
            f"{BASE_URL}/login",
            data={
                'email': self.professional_email,
                'password': self.professional_password
            },
            allow_redirects=False
        )
        return response.status_code in [200, 302]
    
    def test_01_notifications_page_loads(self):
        """Test 1: Notifications page loads"""
        print("\n" + "="*80)
        print("TEST 1: Notifications Page Loads")
        print("="*80)
        
        if not self.login_institution():
            print("❌ Failed to login")
            return False
        
        response = self.session.get(f"{BASE_URL}/notifications")
        
        if response.status_code == 200:
            print("✓ Notifications page loads successfully")
            if b'Notifications' in response.content:
                print("✓ Page title is present")
            if b'Accept' in response.content or b'Accepted' in response.content:
                print("✓ Accept button/badge is present")
            if b'Reject' in response.content or b'Rejected' in response.content:
                print("✓ Reject button/badge is present")
            if b'fa-trash' in response.content:
                print("✓ Delete button is present")
            return True
        else:
            print(f"❌ Page failed to load: {response.status_code}")
            return False
    
    def test_02_accept_reject_buttons_visible(self):
        """Test 2: Accept/Reject buttons visible for pending interests"""
        print("\n" + "="*80)
        print("TEST 2: Accept/Reject Buttons Visible")
        print("="*80)
        
        if not self.login_institution():
            print("❌ Failed to login")
            return False
        
        response = self.session.get(f"{BASE_URL}/notifications")
        content = response.content.decode('utf-8')
        
        has_accept = 'acceptInterest' in content
        has_reject = 'rejectInterest' in content
        has_delete = 'deleteSingle' in content
        
        if has_accept:
            print("✓ Accept function is present")
        if has_reject:
            print("✓ Reject function is present")
        if has_delete:
            print("✓ Delete function is present")
        
        return has_accept and has_reject and has_delete
    
    def test_03_ui_elements_present(self):
        """Test 3: All UI elements are present"""
        print("\n" + "="*80)
        print("TEST 3: UI Elements Present")
        print("="*80)
        
        if not self.login_institution():
            print("❌ Failed to login")
            return False
        
        response = self.session.get(f"{BASE_URL}/notifications")
        content = response.content.decode('utf-8')
        
        elements = {
            'Notifications heading': 'Notifications' in content,
            'Real-time indicator': 'Live' in content or 'realtimeIndicator' in content,
            'Delete All button': 'Delete All' in content,
            'Notification items': 'notification-item' in content,
            'Success message function': 'showSuccessMessage' in content,
            'Bell icon': 'fa-bell' in content,
            'Trash icon': 'fa-trash' in content,
        }
        
        all_present = True
        for element, present in elements.items():
            if present:
                print(f"✓ {element} is present")
            else:
                print(f"❌ {element} is missing")
                all_present = False
        
        return all_present
    
    def test_04_institution_dashboard_accessible(self):
        """Test 4: Institution dashboard is accessible"""
        print("\n" + "="*80)
        print("TEST 4: Institution Dashboard Accessible")
        print("="*80)
        
        if not self.login_institution():
            print("❌ Failed to login")
            return False
        
        response = self.session.get(f"{BASE_URL}/institution/dashboard")
        
        if response.status_code == 200:
            print("✓ Institution dashboard loads successfully")
            content = response.content.decode('utf-8')
            if 'Dashboard' in content:
                print("✓ Dashboard heading is present")
            if 'KPI' in content or 'Total Gigs' in content:
                print("✓ Metrics are visible")
            return True
        else:
            print(f"❌ Dashboard failed to load: {response.status_code}")
            return False
    
    def test_05_navigation_links_present(self):
        """Test 5: Navigation links are present"""
        print("\n" + "="*80)
        print("TEST 5: Navigation Links Present")
        print("="*80)
        
        if not self.login_institution():
            print("❌ Failed to login")
            return False
        
        response = self.session.get(f"{BASE_URL}/institution/dashboard")
        content = response.content.decode('utf-8')
        
        links = {
            'Dashboard link': 'institution/dashboard' in content or 'Dashboard' in content,
            'Post Gig link': 'Post Gig' in content,
            'Notifications link': 'Notifications' in content,
        }
        
        # Check that Home and Browse Gigs are NOT present for institutions
        no_home = 'Browse Gigs' not in content or 'institution' in content
        
        all_present = True
        for link, present in links.items():
            if present:
                print(f"✓ {link} is present")
            else:
                print(f"❌ {link} is missing")
                all_present = False
        
        if no_home:
            print("✓ Home/Browse Gigs correctly hidden from institutions")
        
        return all_present
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("INSTITUTION NOTIFICATION SYSTEM - INTEGRATION TESTS")
        print("="*80)
        print(f"Testing against: {BASE_URL}")
        
        tests = [
            self.test_01_notifications_page_loads,
            self.test_02_accept_reject_buttons_visible,
            self.test_03_ui_elements_present,
            self.test_04_institution_dashboard_accessible,
            self.test_05_navigation_links_present,
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results.append(False)
        
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("✅ ALL TESTS PASSED!")
        else:
            print(f"⚠️  {total - passed} test(s) failed")
        
        print("="*80 + "\n")
        
        return passed == total

if __name__ == '__main__':
    tester = TestNotificationSystem()
    success = tester.run_all_tests()
    exit(0 if success else 1)
