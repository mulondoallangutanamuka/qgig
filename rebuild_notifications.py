"""
Complete Notification System Rebuild Script
Drops and recreates the notifications table with proper schema
"""
import sys
sys.path.insert(0, '.')

from app.database import engine, SessionLocal
from sqlalchemy import text

print("="*80)
print("NOTIFICATION SYSTEM REBUILD")
print("="*80)

db = SessionLocal()

try:
    # Step 1: Drop existing notifications table
    print("\n1. Dropping existing notifications table...")
    db.execute(text("DROP TABLE IF EXISTS notifications"))
    db.commit()
    print("   ✓ Notifications table dropped")
    
    # Step 2: Recreate notifications table with proper schema
    print("\n2. Creating new notifications table...")
    create_table_sql = """
    CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title VARCHAR(200) NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0 NOT NULL,
        job_interest_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (job_interest_id) REFERENCES job_interests(id) ON DELETE CASCADE
    )
    """
    db.execute(text(create_table_sql))
    db.commit()
    print("   ✓ Notifications table created")
    
    # Step 3: Create indexes for performance
    print("\n3. Creating indexes...")
    db.execute(text("CREATE INDEX idx_notifications_user_id ON notifications(user_id)"))
    db.execute(text("CREATE INDEX idx_notifications_job_interest_id ON notifications(job_interest_id)"))
    db.execute(text("CREATE INDEX idx_notifications_created_at ON notifications(created_at)"))
    db.commit()
    print("   ✓ Indexes created")
    
    # Step 4: Verify table structure
    print("\n4. Verifying table structure...")
    result = db.execute(text("PRAGMA table_info(notifications)"))
    columns = result.fetchall()
    print("   Columns:")
    for col in columns:
        print(f"     - {col[1]} ({col[2]})")
    
    print("\n" + "="*80)
    print("✓ NOTIFICATION TABLE REBUILD COMPLETE")
    print("="*80)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    db.rollback()
finally:
    db.close()

print("\nNext steps:")
print("1. Notification model will be recreated")
print("2. Routes will be rebuilt")
print("3. Template will be rebuilt")
print("4. Test with new notifications")
