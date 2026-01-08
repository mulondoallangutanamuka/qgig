# Supabase Migration Guide for QGIG

## Step 1: Supabase Setup ✅
- [ ] Create Supabase account
- [ ] Create new project: `qgig-database`
- [ ] Save database password securely
- [ ] Copy connection string

## Step 2: Export from Render
- [ ] Connect to Render database
- [ ] Export data using pg_dump
- [ ] Save SQL file locally

## Step 3: Import to Supabase
- [ ] Access Supabase SQL Editor
- [ ] Run import script
- [ ] Verify tables and data

## Step 4: Update Configuration
- [ ] Update DATABASE_URL environment variable
- [ ] Test local connection
- [ ] Update deployment config

## Step 5: Deploy and Test
- [ ] Deploy to production
- [ ] Test all database operations
- [ ] Monitor performance

## Connection String Format:
```
postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```
