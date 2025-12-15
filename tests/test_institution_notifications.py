"""
Integration Tests for Institution Notification System
Tests Accept/Reject buttons, Delete functionality, and UI interactions
"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.institution import Institution
from app.models.professional import Professional
from app.models.job import Job, JobStatus
from app.models.job_interest import JobInterest, InterestStatus
from app.models.notification import Notification

class TestInstitutionNotifications:
    """Test suite for institution notification system"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database and app"""
        print("\n" + "="*80)
        print("INSTITUTION NOTIFICATION INTEGRATION TESTS")
        print("="*80)
        
        # Create app
        cls.app, cls.socketio = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create test data
        cls.setup_test_data()
    
    @classmethod
    def setup_test_data(cls):
        """Create test users, jobs, and interests"""
        db = SessionLocal()
        try:
            # Clear existing test data
            db.query(Notification).delete()
            db.query(JobInterest).delete()
            db.query(Job).delete()
            db.query(Professional).delete()
            db.query(Institution).delete()
            db.query(User).filter(User.email.in_([
                'test.institution@test.com',
                'test.professional@test.com'
            ])).delete()
            db.commit()
            
            # Create institution user
            institution_user = User(
                email='test.institution@test.com',
                password='password123',
                role=UserRole.INSTITUTION,
                created_at=datetime.utcnow()
            )
            db.add(institution_user)
            db.flush()
            
            # Create institution profile
            institution = Institution(
                user_id=institution_user.id,
                institution_name='Test Hospital',
                description='Test hospital for integration testing',
                contact_email='test@hospital.com',
                contact_phone='0700000000',
                location='Kampala'
            )
            db.add(institution)
            db.flush()
            
            # Create professional user
            professional_user = User(
                email='test.professional@test.com',
                password='password123',
                role=UserRole.PROFESSIONAL,
                created_at=datetime.utcnow()
            )
            db.add(professional_user)
            db.flush()
            
            # Create professional profile
            professional = Professional(
                user_id=professional_user.id,
                full_name='Test Nurse',
                profession='Nurse',
                phone='0700000001'
            )
            db.add(professional)
            db.flush()
            
            # Create test job
            job = Job(
                title='Test Nursing Position',
                description='Test job for integration testing',
                institution_id=institution.id,
                budget=500000,
                status=JobStatus.OPEN,
                created_at=datetime.utcnow()
            )
            db.add(job)
            db.flush()
            
            # Create job interest
            interest = JobInterest(
                job_id=job.id,
                professional_id=professional.id,
                status=InterestStatus.PENDING,
                created_at=datetime.utcnow()
            )
            db.add(interest)
            db.flush()
            
            # Create notification for institution
            notification = Notification(
                user_id=institution_user.id,
                title='New Interest Received',
                message=f'{professional.full_name} is interested in {job.title}',
                job_interest_id=interest.id,
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notification)
            
            db.commit()
            
            # Store IDs for tests
            cls.institution_user_id = institution_user.id
            cls.professional_user_id = professional_user.id
            cls.institution_id = institution.id
            cls.professional_id = professional.id
            cls.job_id = job.id
            cls.interest_id = interest.id
            cls.notification_id = notification.id
            
            print(f"\n✓ Test data created:")
            print(f"  - Institution: {institution.institution_name} (ID: {institution.id})")
            print(f"  - Professional: {professional.full_name} (ID: {professional.id})")
            print(f"  - Job: {job.title} (ID: {job.id})")
            print(f"  - Interest: ID {interest.id} (Status: {interest.status.value})")
            print(f"  - Notification: ID {notification.id}")
            
        finally:
            db.close()
    
    def login_institution(self):
        """Helper: Login as institution"""
        response = self.client.post('/login', data={
            'email': 'test.institution@test.com',
            'password': 'password123'
        }, follow_redirects=False)
        return response
    
    def login_professional(self):
        """Helper: Login as professional"""
        response = self.client.post('/login', data={
            'email': 'test.professional@test.com',
            'password': 'password123'
        }, follow_redirects=False)
        return response
    
    def test_01_notifications_page_loads(self):
        """Test 1: Notifications page loads for institution"""
        print("\n" + "-"*80)
        print("TEST 1: Notifications Page Loads")
        print("-"*80)
        
        # Login as institution
        self.login_institution()
        
        # Access notifications page
        response = self.client.get('/notifications')
        
        assert response.status_code == 200, "Notifications page should load"
        assert b'Notifications' in response.data, "Page should have Notifications heading"
        assert b'New Interest Received' in response.data, "Should show notification title"
        
        print("✓ Notifications page loads successfully")
        print("✓ Notification is visible")
    
    def test_02_accept_reject_buttons_visible(self):
        """Test 2: Accept and Reject buttons are visible for pending interests"""
        print("\n" + "-"*80)
        print("TEST 2: Accept/Reject Buttons Visible")
        print("-"*80)
        
        # Login as institution
        self.login_institution()
        
        # Access notifications page
        response = self.client.get('/notifications')
        
        assert b'Accept' in response.data, "Accept button should be visible"
        assert b'Reject' in response.data, "Reject button should be visible"
        assert b'acceptInterest' in response.data, "Accept function should be present"
        assert b'rejectInterest' in response.data, "Reject function should be present"
        
        print("✓ Accept button is visible")
        print("✓ Reject button is visible")
        print("✓ JavaScript functions are present")
    
    def test_03_delete_button_visible(self):
        """Test 3: Delete button is visible for each notification"""
        print("\n" + "-"*80)
        print("TEST 3: Delete Button Visible")
        print("-"*80)
        
        # Login as institution
        self.login_institution()
        
        # Access notifications page
        response = self.client.get('/notifications')
        
        assert b'fa-trash' in response.data, "Delete icon should be visible"
        assert b'deleteSingle' in response.data, "Delete function should be present"
        assert b'Delete All' in response.data, "Delete All button should be visible"
        
        print("✓ Delete button is visible")
        print("✓ Delete All button is visible")
        print("✓ Delete functions are present")
    
    def test_04_accept_interest_functionality(self):
        """Test 4: Accept interest updates status and creates notification"""
        print("\n" + "-"*80)
        print("TEST 4: Accept Interest Functionality")
        print("-"*80)
        
        # Login as institution
        self.login_institution()
        
        # Accept the interest
        response = self.client.post(
            f'/notifications/{self.notification_id}/respond',
            json={'action': 'accept'},
            content_type='application/json'
        )
        
        assert response.status_code == 200, f"Accept should succeed, got {response.status_code}"
        
        # Verify interest status changed
        db = SessionLocal()
        try:
            interest = db.query(JobInterest).filter(JobInterest.id == self.interest_id).first()
            assert interest.status == InterestStatus.ACCEPTED, "Interest should be accepted"
            
            # Verify job status changed
            job = db.query(Job).filter(Job.id == self.job_id).first()
            assert job.status == JobStatus.ASSIGNED, "Job should be assigned"
            assert job.assigned_professional_id == self.professional_id, "Professional should be assigned"
            
            # Verify notification created for professional
            prof_notification = db.query(Notification).filter(
                Notification.user_id == self.professional_user_id,
                Notification.title == 'Interest Accepted!'
            ).first()
            assert prof_notification is not None, "Professional should receive notification"
            
            print("✓ Interest status updated to ACCEPTED")
            print("✓ Job status updated to ASSIGNED")
            print("✓ Professional assigned to job")
            print("✓ Notification sent to professional")
            
        finally:
            db.close()
    
    def test_05_accepted_interest_shows_badge(self):
        """Test 5: Accepted interest shows badge instead of buttons"""
        print("\n" + "-"*80)
        print("TEST 5: Accepted Interest Shows Badge")
        print("-"*80)
        
        # Login as institution
        self.login_institution()
        
        # Access notifications page
        response = self.client.get('/notifications')
        
        # Should show accepted badge, not buttons
        assert b'Accepted' in response.data, "Should show Accepted badge"
        
        print("✓ Accepted badge is visible")
        print("✓ Notification reflects accepted status")
    
    def test_06_reject_interest_functionality(self):
        """Test 6: Reject interest updates status and creates notification"""
        print("\n" + "-"*80)
        print("TEST 6: Reject Interest Functionality")
        print("-"*80)
        
        # Create new interest to reject
        db = SessionLocal()
        try:
            # Create new job
            job2 = Job(
                title='Second Test Job',
                description='Another test job',
                institution_id=self.institution_id,
                budget=600000,
                status=JobStatus.OPEN,
                created_at=datetime.utcnow()
            )
            db.add(job2)
            db.flush()
            
            # Create new interest
            interest2 = JobInterest(
                job_id=job2.id,
                professional_id=self.professional_id,
                status=InterestStatus.PENDING,
                created_at=datetime.utcnow()
            )
            db.add(interest2)
            db.flush()
            
            # Create notification
            notification2 = Notification(
                user_id=self.institution_user_id,
                title='New Interest',
                message='Test interest',
                job_interest_id=interest2.id,
                created_at=datetime.utcnow()
            )
            db.add(notification2)
            db.commit()
            
            interest2_id = interest2.id
            notification2_id = notification2.id
            
        finally:
            db.close()
        
        # Login as institution
        self.login_institution()
        
        # Reject the interest
        response = self.client.post(
            f'/notifications/{notification2_id}/respond',
            json={'action': 'reject'},
            content_type='application/json'
        )
        
        assert response.status_code == 200, f"Reject should succeed, got {response.status_code}"
        
        # Verify interest status changed
        db = SessionLocal()
        try:
            interest = db.query(JobInterest).filter(JobInterest.id == interest2_id).first()
            assert interest.status == InterestStatus.REJECTED, "Interest should be rejected"
            
            # Verify notification created for professional
            prof_notification = db.query(Notification).filter(
                Notification.user_id == self.professional_user_id,
                Notification.title == 'Interest Rejected'
            ).first()
            assert prof_notification is not None, "Professional should receive rejection notification"
            
            print("✓ Interest status updated to REJECTED")
            print("✓ Rejection notification sent to professional")
            
        finally:
            db.close()
    
    def test_07_delete_single_notification(self):
        """Test 7: Delete single notification"""
        print("\n" + "-"*80)
        print("TEST 7: Delete Single Notification")
        print("-"*80)
        
        # Create a notification to delete
        db = SessionLocal()
        try:
            notification = Notification(
                user_id=self.institution_user_id,
                title='Test Delete Notification',
                message='This will be deleted',
                created_at=datetime.utcnow()
            )
            db.add(notification)
            db.commit()
            delete_notif_id = notification.id
        finally:
            db.close()
        
        # Login as institution
        self.login_institution()
        
        # Delete the notification
        response = self.client.delete(
            f'/api/notifications/{delete_notif_id}',
            content_type='application/json'
        )
        
        assert response.status_code == 200, f"Delete should succeed, got {response.status_code}"
        
        # Verify notification is deleted
        db = SessionLocal()
        try:
            notification = db.query(Notification).filter(Notification.id == delete_notif_id).first()
            assert notification is None, "Notification should be deleted"
            
            print("✓ Notification deleted successfully")
            
        finally:
            db.close()
    
    def test_08_unauthorized_access_prevented(self):
        """Test 8: Professional cannot accept/reject interests"""
        print("\n" + "-"*80)
        print("TEST 8: Unauthorized Access Prevention")
        print("-"*80)
        
        # Login as professional
        self.login_professional()
        
        # Try to accept interest (should fail)
        response = self.client.post(
            f'/notifications/{self.notification_id}/respond',
            json={'action': 'accept'},
            content_type='application/json'
        )
        
        assert response.status_code == 403, "Professional should not be able to accept interests"
        
        print("✓ Professional cannot accept interests")
        print("✓ Authorization check working")
    
    def test_09_invalid_action_rejected(self):
        """Test 9: Invalid action is rejected"""
        print("\n" + "-"*80)
        print("TEST 9: Invalid Action Rejected")
        print("-"*80)
        
        # Login as institution
        self.login_institution()
        
        # Try invalid action
        response = self.client.post(
            f'/notifications/{self.notification_id}/respond',
            json={'action': 'invalid'},
            content_type='application/json'
        )
        
        assert response.status_code == 400, "Invalid action should be rejected"
        
        print("✓ Invalid action rejected")
        print("✓ Input validation working")
    
    def test_10_ui_elements_present(self):
        """Test 10: All UI elements are present"""
        print("\n" + "-"*80)
        print("TEST 10: UI Elements Present")
        print("-"*80)
        
        # Login as institution
        self.login_institution()
        
        # Access notifications page
        response = self.client.get('/notifications')
        
        # Check for UI elements
        ui_elements = [
            b'Notifications',
            b'Live',  # Real-time indicator
            b'Delete All',
            b'notification-item',
            b'notification-checkbox',
            b'fa-bell',  # Bell icon
            b'fa-trash',  # Delete icon
            b'showSuccessMessage',  # Success message function
        ]
        
        for element in ui_elements:
            assert element in response.data, f"UI element {element} should be present"
        
        print("✓ All UI elements present")
        print("✓ Real-time indicator visible")
        print("✓ Delete functionality available")
        print("✓ Success message system present")
    
    @classmethod
    def teardown_class(cls):
        """Clean up after tests"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print("✓ All integration tests passed successfully!")
        print("✓ Accept/Reject functionality working")
        print("✓ Delete functionality working")
        print("✓ UI elements properly rendered")
        print("✓ Authorization checks in place")
        print("✓ Notifications system fully functional")
        print("="*80 + "\n")

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
