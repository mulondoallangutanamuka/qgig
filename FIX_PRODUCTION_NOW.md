# Fix Production Database - Simple Steps

## 🎯 You Have 3 Easy Options

---

## ✅ OPTION 1: Use Python Script (Easiest)

I've created a script that will do everything for you.

### Steps:

1. **Get your database URL from Render:**
   - Go to https://dashboard.render.com
   - Click on your **PostgreSQL database**
   - Scroll to **Connections** section
   - Copy the **External Database URL**

2. **Install psycopg2 (if not already installed):**
   ```bash
   pip install psycopg2-binary
   ```

3. **Run the migration script:**
   ```bash
   python run_production_migration.py
   ```

4. **Paste your database URL when prompted**

Done! The script will add the missing column automatically.

---

## ✅ OPTION 2: Copy/Paste SQL (Very Easy)

### Steps:

1. **Get your database URL** (same as Option 1)

2. **Install pgAdmin** (free PostgreSQL client):
   - Download from: https://www.pgadmin.org/download/
   - Install and open it

3. **Connect to your database:**
   - Right-click "Servers" → "Register" → "Server"
   - In "Connection" tab, paste your database details from the URL
   - Click "Save"

4. **Open Query Tool:**
   - Right-click your database → "Query Tool"

5. **Copy and paste this SQL:**
   ```sql
   ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expiry_date TIMESTAMP;
   CREATE INDEX IF NOT EXISTS ix_jobs_expiry_date ON jobs (expiry_date);
   UPDATE alembic_version SET version_num = '14a8ca2ff8af';
   ```

6. **Click Execute (F5)**

Done!

---

## ✅ OPTION 3: Auto-Fix on Next Deploy (No Database Access Needed)

If you can't connect to the database at all, use this method:

### Steps:

1. **Go to Render Dashboard** → Your **qgig-backend** service

2. **Click "Settings"**

3. **Find "Start Command"** and change it to:
   ```bash
   python -c "from app.database import engine; from app.models.job import Job; from sqlalchemy import inspect; insp = inspect(engine); cols = [c['name'] for c in insp.get_columns('jobs')]; exec('from sqlalchemy import Column, DateTime; engine.execute(\"ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expiry_date TIMESTAMP\")' if 'expiry_date' not in cols else 'pass')" && gunicorn --worker-class eventlet -w 1 main:app
   ```

   **OR simpler version:**
   ```bash
   alembic upgrade head && gunicorn --worker-class eventlet -w 1 main:app
   ```

4. **Click "Save Changes"**

5. **Click "Manual Deploy" → "Deploy latest commit"**

The migration will run automatically when the service starts!

---

## 🔍 Which Option Should You Choose?

- **Have Python installed?** → Use Option 1 (Python script)
- **Comfortable with SQL tools?** → Use Option 2 (pgAdmin)
- **Can't access database?** → Use Option 3 (Auto-deploy)

---

## ✅ Verification

After using any option, visit:
**https://qgig-backend.onrender.com**

The site should load without errors!

---

## 📞 Still Having Issues?

The SQL you need is just this ONE line:
```sql
ALTER TABLE jobs ADD COLUMN expiry_date TIMESTAMP;
```

Run that anywhere you can execute SQL on your Render PostgreSQL database and you're done!
