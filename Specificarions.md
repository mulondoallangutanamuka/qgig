**Python Backend Edition (Flask/FastAPI + PesaPal Payments)**
**Version 1.1**
**Date:** December 2025

---

# 1. Introduction

## 1.1 Purpose

This Software Requirements Specification describes the full functional and technical specifications for **Qgig**, a web-based on-demand substitute platform that connects institutions (schools, clinics, hospitals, households) with verified professionals (teachers, nurses, caregivers) in Uganda.

The SRS is intended for:

* Developers
* UI/UX designers
* QA and testers
* Technical leads
* Stakeholders & founders

## 1.2 Scope

Qgig enables:

* User authentication & role management
* Professional profile creation
* Institution account creation
* Job posting & job acceptance
* Secure payments through **PesaPal Mobile Money API**
* Ratings & reviews
* Credential verification system
* Admin dashboard
* PostgreSQL-backed data persistence
* Python API serving all client interactions

**Technology Stack (Confirmed):**

* **Backend:** Python (Flask or FastAPI)
* **Database:** PostgreSQL + SQLAlchemy
* **Payments:** **PesaPal Mobile Money & Card API**
* **Hosting:** Render / Railway / Fly.io
* **Frontend:** Flask templates or separate JS frontend

---

# 2. System Overview

Qgig is a multi-role platform with:

* **Institutions** posting jobs
* **Professionals** accepting jobs
* **PesaPal** processing payments
* **Admins** verifying users & managing the system

The backend is a REST API built in Python.

---

# 3. System Architecture

## 3.1 High-Level Architecture

```
[Browser Client]
      |
      v
[Python Backend: Flask/FastAPI]
      |
 SQLAlchemy ORM
      |
[PostgreSQL Database]
      |
Payment Layer (PesaPal REST API)
      |
[MTN / Airtel Mobile Money & Card Payments]
```

## 3.2 Subsystem Overview

* **Authentication Subsystem**
* **Professional Profile Subsystem**
* **Institution Subsystem**
* **Job Management Subsystem**
* **Payment Subsystem (PesaPal)**
* **Verification Subsystem**
* **Ratings & Reviews Subsystem**
* **Admin Management Subsystem**

---

# 4. User Classes & Characteristics

## 4.1 Professional

* Creates profile
* Uploads credentials
* Accepts jobs
* Gets rated

## 4.2 Institution

* Creates institution profile
* Posts jobs
* Pays using PesaPal
* Rates professionals

## 4.3 Admin

* Approves/rejects verification documents
* Manages jobs
* Suspends users
* Views system statistics

---

# 5. Functional Requirements

---

## **5.1 Authentication & Identity Management**

### Description

Users register, log in, and manage their accounts using secure Python-based JWT auth.

### Requirements

* Register with email + phone
* Login with email + password
* JWT tokens for access
* Role assignment: Institution or Professional
* Password hashing (bcrypt)

### Data Model

`users`

* id, name, email, phone, password_hash, role, created_at

---

## **5.2 Professional Profile**

### Requirements

* Bio, subjects/skills, hourly/daily rate
* Upload documents (NIN, certificate, license)
* View verification status

### Data Model

`professionals`

* id, user_id, bio, skills, rate, verified

`documents`

* id, professional_id, file_url, doc_type, status

---

## **5.3 Institution Profile**

### Requirements

* Name, institution type, location
* Contact person
* Post and manage jobs

### Data Model

`institutions`

* id, user_id, name, type, address, contact

---

## **5.4 Job Posting System**

### Requirements

* Create job with role, description, time, rate
* Edit or delete job
* Professionals browse available jobs

### Data Model

`jobs`

* id, institution_id, role, description, date, time, rate, status

---

## **5.5 Job Matching (Phase 1)**

### Requirements

* Basic matching by:

  * Skills
  * Role
  * Availability
* Ranking formula:

```
score = 0.5(skill_match) + 0.3(experience) + 0.2(rating)
```

---

## **5.6 Job Acceptance Workflow**

### Requirements

* Professionals accept jobs
* System locks job so only 1 pro can accept
* Institution notified

### Data Model

`job_assignees`

* job_id, professional_id

---

# **6. Payment System — PesaPal Integration**

Qgig uses **PesaPal Mobile Money** for:

* MTN Mobile Money
* Airtel Money
* Visa/Mastercard (optional)

## 6.1 PesaPal API Flow

### 1. Institution initiates payment

Backend calls:

```
POST /api/transactions/submitOrderRequest
```

### 2. PesaPal returns a checkout URL or mobile money push

### 3. Institution completes payment on phone

### 4. PesaPal sends **Webhook Callback** to Qgig Python backend

### 5. Backend updates DB transaction + job status

---

## 6.2 Functional Requirements

* Generate order request
* Redirect user or trigger STK push
* Save transaction with status:

  * pending
  * completed
  * failed
* Webhook handler validates signature
* Mark job as “Paid”

---

## 6.3 Data Model

`transactions`

* id, job_id, user_id, pesapal_reference, amount, status, payment_method

---

# 7. Ratings & Reviews

### Requirements

* Both parties must rate after job completion
* Ratings affect future matching
* 1–5 star system

### Data Model

`ratings`

* id, job_id, rater_id, ratee_id, stars, comment

---

# 8. Notifications

### Requirements

* Email notifications (job accepted, payment received)
* In-app notifications
* Optional SMS (future)

---

# 9. Admin Dashboard

### Features

* Verify/reject documents
* View pending professionals
* Suspend/activate users
* View platform metrics:

  * total jobs
  * completed jobs
  * payments
  * institutions & professionals

---

# 10. Database Schema (Condensed ERD)

```
Users (1)──(1) Professionals
  │
  └──(1) Institutions

Institutions (1)──(∞) Jobs ──(1)── JobAssignees ──(1)── Professionals

Jobs (1)──(∞) Transactions  
Jobs (1)──(∞) Ratings  
Professionals (1)──(∞) Documents
```

---

# 11. Non-Functional Requirements

## 11.1 Performance

* API request avg < 250ms
* Payment webhook processed < 5s
* DB indexed on jobs, users, and transactions

## 11.2 Security

* JWT authentication
* Strict password hashing
* HTTPS only
* PesaPal signature validation
* Input sanitization

## 11.3 Reliability

* Automatic retry for failed payment verification
* Daily DB backups
* 99%+ uptime target

## 11.4 Maintainability

* Modular Python code
* SQLAlchemy 2.0 models
* Alembic migrations
* Clear folder structure

## 11.5 Scalability

* Backend scales horizontally
* PostgreSQL can scale to millions of rows
* Payment system offloads heavy operations to PesaPal

---

# 12. Compliance Requirements

Qgig must adhere to:

### Uganda Data Protection & Privacy Act (2019)

* Consent screen at signup
* Secure handling of NIN documents
* Right to delete account data
* Access control for sensitive fields

### Payment Regulations

* PesaPal provides PCI-DSS compliance
* Keep logs of all transactions
* Protect API keys with environment variables

---

# 13. Future Enhancements (Phase 2+)

* AI job matching
* Real-time chat between users
* Attendance system (QR code)
* Automated invoicing
* Mobile app (React Native)

---

# 14. Glossary

* **PesaPal:** Online payment aggregator for Africa
* **Webhook:** Callback sent from PesaPal to confirm payment
* **Professional:** Substitute worker
* **Institution:** Client posting a job
* **Job:** Temporary shift
* **JWT:** JSON Web Token (authentication)
* **ORM:** Object Relational Mapper

---