# Comprehensive Professional Profile System - Implementation Plan

## Overview
This document outlines the complete implementation of a professional profile system with secure file uploads, health profession validation, institution rating system, analytics integration, real-time notifications, and E2E testing.

## Current State Analysis

### Existing Models:
- ✅ Professional model (has basic fields, needs enhancement)
- ✅ Rating model (exists, needs verification)
- ✅ Document model (needs review)
- ✅ Job, Institution, User models

### Missing Components:
- Phone number field for professionals
- Issuing body field for registration
- Profession category (Health, IT, Engineering, etc.)
- Secure file upload endpoints
- File access control
- Rating submission after gig completion
- Rating display on profiles
- Analytics integration for ratings
- Socket.IO notifications for profile views and ratings
- E2E Playwright tests

## Implementation Phases

### Phase 1: Database Schema & Models (Priority: HIGH)
**Tasks:**
1. Update Professional model:
   - Add phone_number (String)
   - Add issuing_body (String) - for regulated professions
   - Rename profession_type to profession_category
   - Add file size and metadata fields
   
2. Create/Update Document model:
   - Link to professional_id
   - Store file_type, file_size, file_path
   - Add upload_date, is_verified
   
3. Update Rating model:
   - Ensure one rating per gig constraint
   - Add feedback field
   - Link to completed gigs only

4. Create migration script for all new fields

### Phase 2: Secure File Upload System (Priority: HIGH)
**Tasks:**
1. Create upload service:
   - MIME type validation (PDF, JPG, PNG only)
   - File size limits (CV: 5MB, Certificates: 2MB each, Profile pic: 1MB)
   - Secure filename generation
   - Virus scanning (optional but recommended)
   
2. Create upload endpoints:
   - POST /api/professional/upload-cv
   - POST /api/professional/upload-certificate
   - POST /api/professional/upload-profile-picture
   - DELETE /api/professional/delete-file/{file_id}
   
3. Implement file access control:
   - Professionals: full access to own files
   - Institutions: access only after accepting professional for gig
   - Admin: full access

### Phase 3: Professional Profile UI (Priority: HIGH)
**Tasks:**
1. Create dedicated profile page:
   - Personal Information section
   - Professional Credentials section
   - File Upload section with drag-and-drop
   - Upload progress indicators
   
2. Add validation:
   - Health/Formal professions require registration number
   - Registration number + issuing body mandatory together
   - CV required before applying to gigs
   
3. Implement file management UI:
   - View uploaded files
   - Replace files
   - Delete files
   - Download files

### Phase 4: Institution Rating System (Priority: HIGH)
**Tasks:**
1. Create rating submission endpoint:
   - POST /api/gigs/{gig_id}/rate-professional
   - Validate gig is completed
   - Validate institution owns the gig
   - Prevent duplicate ratings
   
2. Create rating UI:
   - Star rating component (1-5 stars)
   - Optional feedback textarea
   - Submit button
   - Show only after gig completion
   
3. Display ratings on professional profile:
   - Average rating (calculated)
   - Total number of ratings
   - Recent feedback (last 5)
   - Hide if no ratings exist

### Phase 5: Analytics Integration (Priority: MEDIUM)
**Tasks:**
1. Add to Institution Analytics dashboard:
   - Average professional rating per gig
   - Top-rated professionals (leaderboard)
   - Rating distribution chart
   - Ratings over time graph
   
2. Create analytics queries:
   - Calculate average ratings
   - Get top performers
   - Rating trends

### Phase 6: Real-Time Notifications (Priority: MEDIUM)
**Tasks:**
1. Socket.IO events:
   - profile_viewed: When institution views professional profile
   - rating_submitted: When institution rates professional
   
2. Notification triggers:
   - Emit after DB commit
   - Send to specific user room
   - Store notification in DB
   
3. Frontend notification handling:
   - Toast notifications
   - Notification bell updates
   - Notification list updates

### Phase 7: Access Control & Security (Priority: HIGH)
**Tasks:**
1. Implement file access middleware:
   - Check user role
   - Verify gig acceptance for CV/certificate access
   - Log access attempts
   
2. Sanitize uploads:
   - Strip EXIF data from images
   - Validate PDF structure
   - Check for embedded scripts
   
3. Protect sensitive data:
   - Encrypt registration numbers at rest
   - Hide registration numbers from public API
   - Audit log for sensitive data access

### Phase 8: E2E Testing with Playwright (Priority: HIGH)
**Tasks:**
1. Setup Playwright:
   - Install dependencies
   - Configure test environment
   - Create test database
   
2. Write test scenarios:
   - Test 1: Professional uploads CV and certificates
   - Test 2: Health professional cannot save without registration
   - Test 3: Institution views profile after accepting gig
   - Test 4: Institution submits rating after gig completion
   - Test 5: Professional sees updated rating
   - Test 6: Refresh preserves uploaded data
   
3. Integrate with server startup:
   - Run tests before server starts
   - Fail server startup if tests fail
   - Generate test reports

## Database Schema Changes

### professionals table:
```sql
ALTER TABLE professionals ADD COLUMN phone_number VARCHAR(20);
ALTER TABLE professionals ADD COLUMN issuing_body VARCHAR(200);
ALTER TABLE professionals RENAME COLUMN profession_type TO profession_category;
```

### documents table (new or update):
```sql
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    professional_id INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- 'cv', 'certificate', 'profile_picture'
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE CASCADE
);
```

### gig_ratings table (verify/update):
```sql
-- Ensure unique constraint exists
ALTER TABLE ratings ADD CONSTRAINT unique_rating_per_gig UNIQUE (gig_id, rater_id);
```

## API Endpoints

### File Upload:
- POST /api/professional/upload-cv
- POST /api/professional/upload-certificate
- POST /api/professional/upload-profile-picture
- DELETE /api/professional/files/{file_id}
- GET /api/professional/files (list own files)

### Profile:
- GET /api/professional/profile/{id}
- PUT /api/professional/profile (update own profile)
- POST /api/professional/profile/validate (validate before save)

### Rating:
- POST /api/gigs/{gig_id}/rate
- GET /api/professional/{id}/ratings
- GET /api/professional/{id}/rating-summary

### Analytics:
- GET /api/institution/analytics/ratings
- GET /api/institution/analytics/top-professionals

## Security Checklist

- [ ] MIME type validation on all uploads
- [ ] File size limits enforced
- [ ] Secure filename generation (UUID)
- [ ] File access control middleware
- [ ] Registration number encryption
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (sanitize all inputs)
- [ ] CSRF protection on forms
- [ ] Rate limiting on upload endpoints
- [ ] Audit logging for sensitive operations

## Testing Checklist

- [ ] Unit tests for file upload service
- [ ] Unit tests for validation logic
- [ ] Integration tests for rating system
- [ ] E2E test: Professional profile creation
- [ ] E2E test: File upload and download
- [ ] E2E test: Health profession validation
- [ ] E2E test: Institution rating submission
- [ ] E2E test: Rating display on profile
- [ ] E2E test: Analytics integration
- [ ] E2E test: Real-time notifications

## Success Criteria

✅ Professional can create complete profile with all fields
✅ File uploads work with drag-and-drop UI
✅ Health professionals cannot save without registration number
✅ CV and certificates only visible to institutions after gig acceptance
✅ Institutions can rate professionals after gig completion
✅ Ratings display correctly on professional profiles
✅ Analytics show rating data
✅ Real-time notifications work via Socket.IO
✅ All E2E tests pass
✅ Server fails to start if tests fail

## Implementation Order

1. **Day 1**: Database schema, models, migrations
2. **Day 2**: File upload service and endpoints
3. **Day 3**: Professional profile UI with file uploads
4. **Day 4**: Rating system (backend + frontend)
5. **Day 5**: Analytics integration
6. **Day 6**: Real-time notifications
7. **Day 7**: E2E tests and security hardening

## Next Steps

1. Review and approve this plan
2. Start with Phase 1: Database Schema & Models
3. Implement each phase sequentially
4. Test thoroughly at each phase
5. Deploy to production after all tests pass

---

**Status**: Ready to begin implementation
**Estimated Time**: 7 days for complete implementation
**Priority**: HIGH - Core feature for platform trust and compliance
