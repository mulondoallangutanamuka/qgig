"""
Test script to create a sample notification with CV and certificates
"""
from app.database import SessionLocal
from app.models.user import User
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.job import Job
from app.models.job_interest import JobInterest
from app.models.notification import Notification
from app.models.document import Document, DocumentType
from app.sockets import send_interest_notification

def create_test_notification():
    db = SessionLocal()
    
    try:
        # Get a professional with documents
        professional = db.query(Professional).first()
        if not professional:
            print("No professional found in database")
            return
        
        # Get an institution
        institution = db.query(Institution).first()
        if not institution:
            print("No institution found in database")
            return
        
        # Get a job
        job = db.query(Job).filter(Job.institution_id == institution.id).first()
        if not job:
            print("No job found for institution")
            return
        
        # Get documents
        cv_doc = db.query(Document).filter(
            Document.professional_id == professional.id,
            Document.document_type == DocumentType.CV
        ).first()
        
        certificates = db.query(Document).filter(
            Document.professional_id == professional.id,
            Document.document_type == DocumentType.CERTIFICATE
        ).all()
        
        print(f"\n=== TEST NOTIFICATION DATA ===")
        print(f"Professional: {professional.full_name} (ID: {professional.id})")
        print(f"Institution: {institution.name} (ID: {institution.id})")
        print(f"Job: {job.title} (ID: {job.id})")
        print(f"CV Found: {cv_doc is not None}")
        if cv_doc:
            print(f"  - File: {cv_doc.file_name}")
            print(f"  - Path: {cv_doc.file_path}")
            print(f"  - Size: {cv_doc.file_size} bytes")
        print(f"Certificates Found: {len(certificates)}")
        for i, cert in enumerate(certificates, 1):
            print(f"  {i}. {cert.file_name} ({cert.file_size} bytes)")
            print(f"     Path: {cert.file_path}")
        
        # Create notification data
        notification_data = {
            'notification_id': 999,  # Test ID
            'job_interest_id': 999,
            'professional_id': professional.id,
            'professional_name': professional.full_name,
            'job_id': job.id,
            'job_title': job.title,
            'institution_id': institution.id,
            'status': 'pending',
            'message': f"TEST: {professional.full_name} has expressed interest in your job: {job.title}",
            'timestamp': '2025-12-15T11:00:00',
            'profile': {
                'full_name': professional.full_name,
                'phone_number': professional.phone_number,
                'location': professional.location,
                'profession_category': professional.profession_category,
                'specialization': professional.specialization,
                'skills': professional.skills,
                'bio': professional.bio,
                'hourly_rate': float(professional.hourly_rate) if professional.hourly_rate else None,
                'daily_rate': float(professional.daily_rate) if professional.daily_rate else None,
                'registration_number': professional.registration_number,
                'issuing_body': professional.issuing_body,
                'experience': professional.experience,
                'education': professional.education,
                'certifications': professional.certifications,
                'profile_picture': professional.profile_picture
            },
            'documents': {
                'cv': {
                    'id': cv_doc.id,
                    'name': cv_doc.file_name,
                    'url': cv_doc.file_path,
                    'size': cv_doc.file_size
                } if cv_doc else None,
                'certificates': [
                    {
                        'id': cert.id,
                        'name': cert.file_name,
                        'url': cert.file_path,
                        'size': cert.file_size
                    } for cert in certificates
                ]
            }
        }
        
        print(f"\n=== SENDING TEST NOTIFICATION ===")
        print(f"To institution ID: {institution.id}")
        print(f"Profile data keys: {list(notification_data['profile'].keys())}")
        print(f"Documents CV: {notification_data['documents']['cv']}")
        print(f"Documents Certificates: {len(notification_data['documents']['certificates'])} items")
        
        # Send notification
        send_interest_notification(institution.id, notification_data)
        
        print(f"\n✅ Test notification sent successfully!")
        print(f"Check the institution's browser for the notification popup")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_notification()
