# Production Database Migration Fix

## Issue
The production database on Render is missing the `expiry_date` column in the `jobs` table, causing the application to crash with:
```
psycopg2.errors.UndefinedColumn: column jobs.expiry_date does not exist
```

## Solution
You need to run the Alembic migration on the production database.

---

## Option 1: Run Migration via Render Shell (Recommended)

### Step 1: Access Render Shell
1. Go to https://dashboard.render.com
2. Navigate to your `qgig-backend` service
3. Click on the **Shell** tab

### Step 2: Run Migration Commands
```bash
# Navigate to project directory
cd /opt/render/project/src

# Run the migration
alembic upgrade head
```

This will apply the migration `14a8ca2ff8af_add_expiry_date_to_jobs.py` which adds the `expiry_date` column.

---

## Option 2: Manual SQL (If Alembic Fails)

If the Alembic migration doesn't work, you can manually add the column using SQL.

### Step 1: Access Database
1. Go to your Render Dashboard
2. Find your PostgreSQL database
3. Click **Connect** and copy the External Database URL

### Step 2: Connect via psql or Database Client
```bash
psql <YOUR_DATABASE_URL>
```

### Step 3: Run SQL Commands
```sql
-- Add the expiry_date column
ALTER TABLE jobs ADD COLUMN expiry_date TIMESTAMP;

-- Create index for better performance
CREATE INDEX ix_jobs_expiry_date ON jobs (expiry_date);

-- Verify the column was added
\d jobs
```

### Step 4: Update Alembic Version (Important!)
After manually running SQL, update the Alembic version table:
```sql
-- Check current version
SELECT * FROM alembic_version;

-- Update to the latest migration version
UPDATE alembic_version SET version_num = '14a8ca2ff8af';
```

---

## Option 3: Add Migration to Render Build Command

### Update Render Build Settings
1. Go to your Render service settings
2. Find the **Build Command** or **Start Command**
3. Update to include migration:

**Current Start Command:**
```bash
gunicorn --worker-class eventlet -w 1 main:app
```

**New Start Command:**
```bash
alembic upgrade head && gunicorn --worker-class eventlet -w 1 main:app
```

This will automatically run migrations on every deployment.

---

## Verification

After running the migration, verify it worked:

### Check via SQL
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'jobs' AND column_name = 'expiry_date';
```

Expected output:
```
 column_name  | data_type 
--------------+-----------
 expiry_date  | timestamp
```

### Check via Application
Visit https://qgig-backend.onrender.com and verify the homepage loads without errors.

---

## Quick Fix Script

Create a file `migrate_production.sh`:
```bash
#!/bin/bash
# Run this on Render shell

cd /opt/render/project/src
alembic upgrade head
echo "Migration complete!"
```

---

## Prevention for Future

To prevent this issue in the future, add migration to your deployment process:

### Update `render.yaml` (if you have one)
```yaml
services:
  - type: web
    name: qgig-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "alembic upgrade head && gunicorn --worker-class eventlet -w 1 main:app"
```

### Or update Render Dashboard Settings
- Build Command: `pip install -r requirements.txt`
- Start Command: `alembic upgrade head && gunicorn --worker-class eventlet -w 1 main:app`

---

## Troubleshooting

### If migration fails with "relation does not exist"
The database might not have the alembic_version table. Initialize it:
```bash
alembic stamp head
alembic upgrade head
```

### If you get permission errors
Make sure your database user has ALTER TABLE permissions.

### If migration is already applied locally but not on production
This is expected. The migration file exists in your code but hasn't been run on the production database yet.

---

## Summary

**Fastest Solution**: 
1. Open Render Shell
2. Run: `cd /opt/render/project/src && alembic upgrade head`
3. Restart your service if needed

**Time Required**: ~2 minutes

**Status After Fix**: ✅ Application will work correctly on production
