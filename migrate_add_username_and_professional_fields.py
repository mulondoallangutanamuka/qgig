"""
Database migration to add username and professional fields
Run this script to update the database schema
"""
import sqlite3
import os

def run_migration():
    # Database is in root directory, not app folder
    db_path = 'qgig.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting migration...")
        
        # Add username column to users table
        print("Adding username column to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN username VARCHAR(50)")
            print("✓ Added username column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Username column already exists")
            else:
                raise
        
        # Add professional fields
        print("\nAdding professional knowledge fields...")
        
        professional_fields = [
            ("education", "TEXT"),
            ("certifications", "TEXT"),
            ("experience", "TEXT"),
            ("specialization", "VARCHAR(200)"),
            ("languages", "VARCHAR(200)"),
            ("cv_file", "VARCHAR(255)"),
            ("certificate_files", "TEXT"),
            ("profile_picture", "VARCHAR(255)")
        ]
        
        for field_name, field_type in professional_fields:
            try:
                cursor.execute(f"ALTER TABLE professionals ADD COLUMN {field_name} {field_type}")
                print(f"✓ Added {field_name} column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"✓ {field_name} column already exists")
                else:
                    raise
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNew columns added:")
        print("  Users table: username")
        print("  Professionals table: education, certifications, experience, specialization,")
        print("                       languages, cv_file, certificate_files, profile_picture")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Username and Professional Fields")
    print("=" * 60)
    print()
    
    run_migration()
    
    print("\n" + "=" * 60)
    print("Migration complete! You can now restart the server.")
    print("=" * 60)
