"""
Database migration script to add new columns to job_interests table
"""
import sys
sys.path.insert(0, '.')

from app.database import engine
from sqlalchemy import text

def migrate():
    print("Running database migration...")
    
    with engine.connect() as conn:
        # Check if institution_id column exists
        try:
            result = conn.execute(text("SELECT institution_id FROM job_interests LIMIT 1"))
            print("✓ institution_id column already exists")
        except Exception:
            print("Adding institution_id column...")
            conn.execute(text("ALTER TABLE job_interests ADD COLUMN institution_id INTEGER REFERENCES institutions(id)"))
            conn.commit()
            print("✓ institution_id column added")
        
        # Update existing interests to have institution_id from their job
        print("Updating existing interests with institution_id...")
        conn.execute(text("""
            UPDATE job_interests 
            SET institution_id = (
                SELECT institution_id FROM jobs WHERE jobs.id = job_interests.job_id
            )
            WHERE institution_id IS NULL
        """))
        conn.commit()
        print("✓ Existing interests updated")
        
        print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
