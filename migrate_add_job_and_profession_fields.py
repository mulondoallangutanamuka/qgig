"""
Database migration to add job_type, sector, profession_type, and registration_number fields
Run this script to update the database schema
"""
import sqlite3
import os

def run_migration():
    # Database is in root directory
    db_path = 'qgig.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting migration...")
        
        # Add job_type and sector columns to jobs table
        print("\nAdding job search fields to jobs table...")
        
        job_fields = [
            ("job_type", "VARCHAR(100)"),
            ("sector", "VARCHAR(100)")
        ]
        
        for field_name, field_type in job_fields:
            try:
                cursor.execute(f"ALTER TABLE jobs ADD COLUMN {field_name} {field_type}")
                print(f"✓ Added {field_name} column to jobs table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"✓ {field_name} column already exists in jobs table")
                else:
                    raise
        
        # Add profession_type and registration_number to professionals table
        print("\nAdding profession fields to professionals table...")
        
        profession_fields = [
            ("profession_type", "VARCHAR(50)"),
            ("registration_number", "VARCHAR(100)")
        ]
        
        for field_name, field_type in profession_fields:
            try:
                cursor.execute(f"ALTER TABLE professionals ADD COLUMN {field_name} {field_type}")
                print(f"✓ Added {field_name} column to professionals table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"✓ {field_name} column already exists in professionals table")
                else:
                    raise
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNew columns added:")
        print("  Jobs table: job_type, sector")
        print("  Professionals table: profession_type, registration_number")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Job Type, Sector, and Profession Fields")
    print("=" * 60)
    print()
    
    run_migration()
    
    print("\n" + "=" * 60)
    print("Migration complete! You can now restart the server.")
    print("=" * 60)
