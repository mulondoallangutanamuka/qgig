#!/usr/bin/env python3
"""
Production Database Migration Script
Run this script to add the expiry_date column to your production database
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def run_migration(database_url):
    """Run the migration to add expiry_date column"""
    
    print("🔄 Connecting to production database...")
    
    try:
        # Parse the database URL
        result = urlparse(database_url)
        
        # Connect to the database
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        print("\n📝 Running migration...")
        
        # Add the expiry_date column
        cursor.execute("""
            ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expiry_date TIMESTAMP;
        """)
        print("  ✓ Added expiry_date column")
        
        # Create index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_jobs_expiry_date ON jobs (expiry_date);
        """)
        print("  ✓ Created index on expiry_date")
        
        # Update alembic version
        cursor.execute("""
            UPDATE alembic_version SET version_num = '14a8ca2ff8af' 
            WHERE version_num IS NOT NULL;
        """)
        print("  ✓ Updated migration version")
        
        # Commit the changes
        conn.commit()
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'jobs' AND column_name = 'expiry_date';
        """)
        
        result = cursor.fetchone()
        
        if result:
            print("\n✅ Migration completed successfully!")
            print(f"   Column: {result[0]}")
            print(f"   Type: {result[1]}")
            print(f"   Nullable: {result[2]}")
            print("\n🎉 Your production database is now up to date!")
            print("   Visit https://qgig-backend.onrender.com to verify")
        else:
            print("\n⚠️  Warning: Column may not have been added")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    """Main function"""
    
    print("=" * 60)
    print("  QGig Production Database Migration")
    print("  Adding expiry_date column to jobs table")
    print("=" * 60)
    print()
    
    # Check if DATABASE_URL is provided
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("Please provide your Render PostgreSQL connection string:")
        print("(You can find this in Render Dashboard → Database → Connections)")
        print()
        database_url = input("Enter DATABASE_URL: ").strip()
    
    if not database_url:
        print("❌ No database URL provided. Exiting.")
        sys.exit(1)
    
    # Run the migration
    success = run_migration(database_url)
    
    if success:
        print("\n" + "=" * 60)
        print("  Migration Complete! ✅")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("  Migration Failed! ❌")
        print("  Please check the error above and try again")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
