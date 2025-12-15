"""
Comprehensive Professional Profile System - Database Migration
Adds all required fields for the new profile system
"""
import sqlite3
import os

def run_migration():
    db_path = 'qgig.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print("COMPREHENSIVE PROFILE SYSTEM MIGRATION")
        print("=" * 70)
        print()
        
        # 1. Update professionals table
        print("1. Updating professionals table...")
        
        professional_fields = [
            ("phone_number", "VARCHAR(20)"),
            ("issuing_body", "VARCHAR(200)"),
            ("profession_category", "VARCHAR(50)")
        ]
        
        for field_name, field_type in professional_fields:
            try:
                cursor.execute(f"ALTER TABLE professionals ADD COLUMN {field_name} {field_type}")
                print(f"   ✓ Added {field_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"   ✓ {field_name} already exists")
                else:
                    raise
        
        # Rename profession_type to profession_category if it exists
        try:
            cursor.execute("SELECT profession_type FROM professionals LIMIT 1")
            # If we get here, profession_type exists, need to migrate data
            print("   → Migrating profession_type to profession_category...")
            cursor.execute("UPDATE professionals SET profession_category = profession_type WHERE profession_type IS NOT NULL")
            print("   ✓ Data migrated")
        except sqlite3.OperationalError:
            print("   ✓ profession_type doesn't exist, using profession_category")
        
        # 2. Update documents table
        print("\n2. Updating documents table...")
        
        document_fields = [
            ("professional_id", "INTEGER"),
            ("file_size", "INTEGER"),
            ("mime_type", "VARCHAR(100)"),
            ("is_verified", "INTEGER DEFAULT 0")
        ]
        
        for field_name, field_type in document_fields:
            try:
                cursor.execute(f"ALTER TABLE documents ADD COLUMN {field_name} {field_type}")
                print(f"   ✓ Added {field_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"   ✓ {field_name} already exists")
                else:
                    raise
        
        # 3. Update ratings table
        print("\n3. Updating ratings table...")
        
        rating_fields = [
            ("institution_id", "INTEGER"),
            ("professional_id", "INTEGER")
        ]
        
        for field_name, field_type in rating_fields:
            try:
                cursor.execute(f"ALTER TABLE ratings ADD COLUMN {field_name} {field_type}")
                print(f"   ✓ Added {field_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"   ✓ {field_name} already exists")
                else:
                    raise
        
        # Rename review to feedback if it exists
        try:
            cursor.execute("SELECT review FROM ratings LIMIT 1")
            print("   → Migrating review to feedback...")
            cursor.execute("UPDATE ratings SET feedback = review WHERE review IS NOT NULL")
            print("   ✓ Data migrated")
        except sqlite3.OperationalError:
            print("   ✓ review doesn't exist, using feedback")
        
        # 4. Create indexes for performance
        print("\n4. Creating indexes...")
        
        indexes = [
            ("idx_documents_professional", "documents", "professional_id"),
            ("idx_ratings_institution", "ratings", "institution_id"),
            ("idx_ratings_professional", "ratings", "professional_id"),
            ("idx_ratings_gig", "ratings", "gig_id")
        ]
        
        for idx_name, table_name, column_name in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name})")
                print(f"   ✓ Created {idx_name}")
            except sqlite3.OperationalError as e:
                print(f"   ✓ {idx_name} already exists")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nChanges applied:")
        print("  • professionals: phone_number, issuing_body, profession_category")
        print("  • documents: professional_id, file_size, mime_type, is_verified")
        print("  • ratings: institution_id, professional_id")
        print("  • indexes: Created for better query performance")
        print("\n" + "=" * 70)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ MIGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
