"""
File Access Control Service
Controls who can access professional documents based on gig acceptance
"""
from typing import Optional, Tuple
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.job import Job, JobStatus
from app.models.job_interest import JobInterest, InterestStatus
from app.models.document import Document, DocumentType

class FileAccessControl:
    """Service for controlling file access based on user roles and gig status"""
    
    @staticmethod
    def can_access_file(user_id: int, document_id: int, db) -> Tuple[bool, Optional[str]]:
        """
        Check if user can access a document
        Returns: (can_access, reason_if_denied)
        """
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False, "Document not found"
        
        # Admin can access everything
        if user.role == UserRole.ADMIN:
            return True, None
        
        # Professional can access their own documents
        if user.role == UserRole.PROFESSIONAL:
            professional = db.query(Professional).filter(Professional.user_id == user_id).first()
            if professional and document.professional_id == professional.id:
                return True, None
            return False, "You can only access your own documents"
        
        # Institution can access documents only after accepting professional for a gig
        if user.role == UserRole.INSTITUTION:
            institution = db.query(Institution).filter(Institution.user_id == user_id).first()
            if not institution:
                return False, "Institution profile not found"
            
            # Check if this institution has accepted this professional for any gig
            professional = db.query(Professional).filter(Professional.id == document.professional_id).first()
            if not professional:
                return False, "Professional not found"
            
            # Check for accepted gigs
            accepted_gig = db.query(JobInterest).join(Job).filter(
                Job.institution_id == institution.id,
                JobInterest.professional_id == professional.id,
                JobInterest.status == InterestStatus.ACCEPTED
            ).first()
            
            if accepted_gig:
                return True, None
            
            return False, "You can only access documents of professionals you have accepted for gigs"
        
        return False, "Unauthorized access"
    
    @staticmethod
    def can_access_professional_profile(viewer_user_id: int, professional_id: int, db) -> Tuple[bool, Optional[str], bool]:
        """
        Check if user can access a professional's profile
        Returns: (can_access, reason_if_denied, can_view_sensitive_data)
        """
        # Get viewer
        viewer = db.query(User).filter(User.id == viewer_user_id).first()
        if not viewer:
            return False, "User not found", False
        
        # Get professional
        professional = db.query(Professional).filter(Professional.id == professional_id).first()
        if not professional:
            return False, "Professional not found", False
        
        # Admin can access everything
        if viewer.role == UserRole.ADMIN:
            return True, None, True
        
        # Professional can access their own profile fully
        if viewer.role == UserRole.PROFESSIONAL:
            viewer_professional = db.query(Professional).filter(Professional.user_id == viewer_user_id).first()
            if viewer_professional and viewer_professional.id == professional_id:
                return True, None, True
            # Can view other professionals' public profiles
            return True, None, False
        
        # Institution can view profiles
        if viewer.role == UserRole.INSTITUTION:
            institution = db.query(Institution).filter(Institution.user_id == viewer_user_id).first()
            if not institution:
                return False, "Institution profile not found", False
            
            # Check if institution has accepted this professional for any gig
            accepted_gig = db.query(JobInterest).join(Job).filter(
                Job.institution_id == institution.id,
                JobInterest.professional_id == professional_id,
                JobInterest.status == InterestStatus.ACCEPTED
            ).first()
            
            # Can view profile, but sensitive data only if accepted
            return True, None, bool(accepted_gig)
        
        return False, "Unauthorized access", False
    
    @staticmethod
    def log_file_access(user_id: int, document_id: int, access_granted: bool, db):
        """Log file access attempts for audit trail"""
        # TODO: Implement audit logging
        # This would log to a separate audit_log table
        pass
    
    @staticmethod
    def can_download_cv(institution_user_id: int, professional_id: int, db) -> bool:
        """Check if institution can download professional's CV"""
        institution = db.query(Institution).filter(Institution.user_id == institution_user_id).first()
        if not institution:
            return False
        
        # Check for accepted gigs
        accepted_gig = db.query(JobInterest).join(Job).filter(
            Job.institution_id == institution.id,
            JobInterest.professional_id == professional_id,
            JobInterest.status == InterestStatus.ACCEPTED
        ).first()
        
        return bool(accepted_gig)
    
    @staticmethod
    def can_download_certificates(institution_user_id: int, professional_id: int, db) -> bool:
        """Check if institution can download professional's certificates"""
        return FileAccessControl.can_download_cv(institution_user_id, professional_id, db)
    
    @staticmethod
    def get_accessible_documents(user_id: int, professional_id: int, db):
        """Get list of documents user can access for a professional"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get all documents for professional
        documents = db.query(Document).filter(Document.professional_id == professional_id).all()
        
        # Filter based on access control
        accessible = []
        for doc in documents:
            can_access, _ = FileAccessControl.can_access_file(user_id, doc.id, db)
            if can_access:
                accessible.append(doc)
        
        return accessible
