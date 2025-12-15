---

# ✅ **Qgig Development TODO List**

### *(Ordered from Easy → Hard, with Acceptance Criteria)*

### **Python Backend + PostgreSQL + SQLAlchemy + PesaPal Edition**

---

# **PHASE 1 — PROJECT FOUNDATION (Easy)**

---

## ✔ **1. Set Up Project Environment**

* [x] Create Python virtual environment
* [x] Install Flask
* [x] Install SQLAlchemy + Alembic
* [ ] Create Git repository
* [x] Setup `.env` file

**Acceptance Criteria:**

* Backend runs locally (`python main.py`)
* Environment variables load correctly
* Database connection established successfully

---

## ✔ **2. Initialize PostgreSQL Database**

* [x] Create PostgreSQL database (local or cloud: Render/Railway)
* [x] Configure SQLAlchemy engine
* [x] Run initial Alembic migration
* [x] Create base models directory

**Acceptance Criteria:**

* Database reachable
* Tables successfully created
* Alembic “revision up” works without errors

---

## ✔ **3. Basic Routing Structure**

* [x] Create main API router
* [x] Setup health-check endpoint
* [x] Implement 404 + error handler

**Acceptance Criteria:**

* Accessing `/health` returns `{status: "ok"}`
* Invalid routes return JSON 404 response
* No server errors

---

# **PHASE 2 — AUTHENTICATION & USER ACCOUNTS (Medium)**

---

## ✔ **4. User Authentication (JWT)**

* [x] Create `users` table
* [x] Implement register endpoint
* [x] Implement login endpoint
* [x] Hash passwords using bcrypt
* [x] Issue JWT tokens
* [x] Protect secured routes with auth middleware

**Acceptance Criteria:**

* User can register with email + password
* User can log in and receive a JWT token
* Protected endpoints reject invalid/missing tokens
* Password is hashed (never stored in plain text)

---

## ✔ **5. Role System (Professional / Institution / Admin)**

* [x] Add `role` column to users
* [x] Add role-based middleware
* [x] Redirect users based on role

**Acceptance Criteria:**

* User must choose “Professional” or “Institution” on signup
* Admin accounts can be created manually
* Role-based restricted routes return 403 for unauthorized roles

---

# **PHASE 3 — USER PROFILES (Medium)**

---

## ✔ **6. Professional Profile System**

* [x] Create `professionals` table
* [x] Add endpoints for:

  * [x] Update profile
  * [x] Add skills/bio
  * [x] Set hourly/daily rate
* [x] Link user ↔ professional

**Acceptance Criteria:**

* Only professionals can create/edit profile
* Profile persists in DB
* GET /professional/profile returns correct info

---

## ✔ **7. Document Upload & Verification**

* [x] Setup file uploads
* [x] Create `documents` table
* [x] Upload NIN, certificate, license
* [x] Admin verifies/rejects documents

**Acceptance Criteria:**

* Supported formats: PDF/JPG/PNG
* File stored securely on server or S3-like storage
* Document status updates (pending/approved/rejected)
* Professional sees verification badge after approval

---

## ✔ **8. Institution Profile**

* [x] Create `institutions` table
* [x] Endpoints to update institution details
* [x] Handle institution contact info

**Acceptance Criteria:**

* Only institution users can create/edit institution profile
* Institution data stored and retrievable
* Profile validation prevents empty required fields

---

# **PHASE 4 — JOB SYSTEM (Harder)**

---

## ✔ **9. Job Posting**

* [x] Create `jobs` table
* [x] Endpoint to create job
* [x] Endpoint to edit/delete job
* [x] List institution’s own jobs

**Acceptance Criteria:**

* Only institutions can post jobs
* Required fields validated
* Job stored in DB with status “Open”

---

## ✔ **10. Job Discovery**

* [x] Endpoint to view available jobs
* [x] Filter jobs by role (teacher/nurse/caregiver)
* [x] Exclude already accepted jobs

**Acceptance Criteria:**

* Professionals see only qualifying jobs
* Jobs appear instantly after posting
* No “accepted” jobs appear in list

---

## ✔ **11. Job Acceptance Workflow**

* [x] Create `job_assignees` table
* [x] Professional accepts job
* [x] Lock job to one professional
* [x] Notify institution (email or system log)

**Acceptance Criteria:**

* Only one professional can accept a job
* Job status changes to “Accepted”
* Institution sees the assigned professional

---

# **PHASE 5 — PAYMENT SYSTEM (Advanced)**

### **Using PesaPal**

---

## ✔ **12. PesaPal Order Creation**

* [x] Set up PesaPal API credentials
* [x] Implement authentication with PesaPal (OAuth token)
* [x] Create endpoint: `/payments/initiate`
* [x] Generate order request via:
  `POST /api/Transactions/SubmitOrderRequest`
* [x] Store transaction as “pending”

**Acceptance Criteria:**

* Institution receives PesaPal payment prompt (Checkout or Mobile Money Push)
* Transaction stored with PesaPal `OrderTrackingId`
* Errors logged clearly

---

## ✔ **13. PesaPal Webhook Handler**

* [x] Create public endpoint: `/payments/webhook`
* [x] Validate signature (if provided)
* [x] Query order status using:
  `GET /api/Transactions/GetTransactionStatus`
* [x] Update job status to “Paid”
* [x] Update transaction status to “Completed”

**Acceptance Criteria:**

* Webhook receives callback from PesaPal sandbox
* Job automatically updates to “Paid”
* Duplicate callbacks gracefully ignored
* Failed payments marked “Failed”

---

# **PHASE 6 — TRUST, REVIEWS & ADMIN PANEL (Hardest)**

---

## ✔ **14. Ratings & Reviews**

* [x] Create `ratings` table
* [x] Add rating modal flow after job completion
* [x] Allow both sides to rate
* [x] Average rating affects job matching

**Acceptance Criteria:**

* Ratings stored per job
* One rating per user per job
* Ratings visible on professional profiles

---

## ✔ **15. Admin Dashboard**

* [x] Admin-only routes
* [x] Verification approval for documents
* [x] User suspension tools
* [x] System metrics:

  * Jobs posted
  * Jobs completed
  * Payments processed
  * Verified professionals

**Acceptance Criteria:**

* Admin login required
* Admin can approve/reject documents
* Admin can suspend/activate accounts
* Metrics load correctly

---

# **PHASE 7 — NON-FUNCTIONAL & FINALIZATION (Expert Level)**

---

## ✔ **16. Security Hardening**

* [x] Enforce HTTPS
* [x] Sanitize all user input
* [x] Enable rate-limiting
* [x] Secure API keys in environment variables
* [x] Restrict file upload size & types

**Acceptance Criteria:**

* Backend passes security scan
* Sensitive keys not exposed
* Only authorized roles can access protected data

---

## ✔ **17. Performance Optimization**

* [x] Add DB indexes
* [x] Optimize job queries
* [x] Add caching layer (optional)
* [x] Stress test with >2000 concurrent requests

**Acceptance Criteria:**

* Average request < 250 ms
* API handles simulated load
* DB handles >10k jobs without slow queries

---