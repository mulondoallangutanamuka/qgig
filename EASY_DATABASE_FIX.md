# Easy Database Fix - No Shell Required

## Quick Fix Using Render Dashboard

Since you can't access the shell, here's the easiest way to fix the production database:

---

## Step 1: Get Your Database Connection String

1. Go to https://dashboard.render.com
2. Click on your **PostgreSQL database** (not the web service)
3. Scroll down to **Connections**
4. Copy the **External Database URL**

It will look like:
```
postgresql://username:password@host.region.render.com/database_name
```

---

## Step 2: Use a Database Client

### Option A: Use Online SQL Tool (Easiest)

1. Go to https://www.pgadmin.org/download/ and download pgAdmin (free)
2. Or use any PostgreSQL client you prefer

### Option B: Use Command Line (If you have PostgreSQL installed)

Open your terminal/PowerShell and run:
```bash
psql "postgresql://your-connection-string-here"
```

### Option C: Use Render's SQL Editor (If Available)

Some Render plans have a built-in SQL editor in the database dashboard.

---

## Step 3: Run This SQL

Copy and paste this exact SQL into your database client:

```sql
-- Add the missing expiry_date column
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expiry_date TIMESTAMP;

-- Create index for performance
CREATE INDEX IF NOT EXISTS ix_jobs_expiry_date ON jobs (expiry_date);

-- Mark migration as complete
UPDATE alembic_version SET version_num = '14a8ca2ff8af' WHERE version_num IS NOT NULL;

-- Verify it worked
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'jobs' AND column_name = 'expiry_date';
```

You should see output like:
```
 column_name  | data_type 
--------------+-----------
 expiry_date  | timestamp
```

---

## Step 4: Restart Your Render Service

1. Go back to your Render dashboard
2. Click on your **qgig-backend** web service
3. Click **Manual Deploy** → **Clear build cache & deploy**

OR just click the **Restart** button if available.

---

## Alternative: Update via Render Environment

If you can't connect to the database directly, you can trigger the migration automatically:

### Update Start Command in Render

1. Go to your **qgig-backend** service in Render
2. Click **Settings**
3. Find **Start Command**
4. Change from:
   ```
   gunicorn --worker-class eventlet -w 1 main:app
   ```
   To:
   ```
   python -c "from app.database import engine, Base; Base.metadata.create_all(engine)" && gunicorn --worker-class eventlet -w 1 main:app
   ```

This will create all missing columns on startup.

---

## Even Simpler: Just Add the Column

If all else fails, here's the absolute minimum SQL you need:

```sql
ALTER TABLE jobs ADD COLUMN expiry_date TIMESTAMP;
```

That's it! Just run that one line in any SQL client connected to your Render database.

---

## Verification

After running the SQL, visit:
https://qgig-backend.onrender.com

The error should be gone and the site should load properly.

---

## Need Help?

If you're having trouble connecting to the database:

1. Make sure you're using the **External Database URL** (not Internal)
2. Check that your IP is allowed (Render usually allows all IPs by default)
3. Try using pgAdmin - it's the most user-friendly option

---

**Time Required**: 5 minutes
**Difficulty**: Easy - just copy/paste SQL
**Result**: Production site will work perfectly ✅
