-- Migration: Add expiry_date column to jobs table
-- This script adds the missing expiry_date column to the production database

-- Add the expiry_date column
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expiry_date TIMESTAMP;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS ix_jobs_expiry_date ON jobs (expiry_date);

-- Verify the column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'jobs' AND column_name = 'expiry_date';

-- Update alembic version to mark this migration as applied
-- (Only run this if you're applying the migration manually via SQL)
-- UPDATE alembic_version SET version_num = '14a8ca2ff8af';
