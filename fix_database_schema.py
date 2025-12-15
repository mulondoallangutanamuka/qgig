"""
Fix database schema mismatches
- Rename ratings.review to ratings.feedback
- Ensure all new columns exist
"""
import sqlite3
import os

def fix_database():
    db_path = 'qgig.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Fixing database schema...")
    
    try:
        # Check if ratings table has 'review' column
        cursor.execute("PRAGMA table_info(ratings)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if 'review' in columns and 'feedback' not in columns:
            print("Renaming ratings.review to ratings.feedback...")
            
            # SQLite doesn't support RENAME COLUMN directly in older versions
            # So we need to recreate the table
            
            # 1. Create new table with correct schema
            cursor.execute("""
                CREATE TABLE ratings_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gig_id INTEGER NOT NULL,
                    institution_id INTEGER,
                    professional_id INTEGER,
                    rater_id INTEGER NOT NULL,
                    rated_id INTEGER NOT NULL,
                    rating REAL NOT NULL,
                    feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (gig_id) REFERENCES jobs(id),
                    FOREIGN KEY (institution_id) REFERENCES institutions(id),
                    FOREIGN KEY (professional_id) REFERENCES professionals(id),
                    FOREIGN KEY (rater_id) REFERENCES users(id),
                    FOREIGN KEY (rated_id) REFERENCES users(id)
                )
            """)
            
            # 2. Copy data from old table to new table
            cursor.execute("""
                INSERT INTO ratings_new 
                (id, gig_id, institution_id, professional_id, rater_id, rated_id, rating, feedback, created_at, updated_at)
                SELECT id, gig_id, institution_id, professional_id, rater_id, rated_id, rating, review, created_at, updated_at
                FROM ratings
            """)
            
            # 3. Drop old table
            cursor.execute("DROP TABLE ratings")
            
            # 4. Rename new table
            cursor.execute("ALTER TABLE ratings_new RENAME TO ratings")
            
            # 5. Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_ratings_gig_id ON ratings(gig_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_ratings_rater_id ON ratings(rater_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_ratings_rated_id ON ratings(rated_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_ratings_institution_id ON ratings(institution_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_ratings_professional_id ON ratings(professional_id)")
            
            print("✅ Successfully renamed ratings.review to ratings.feedback")
        else:
            print("✅ ratings.feedback column already exists or review column not found")
        
        # Check professionals table for profession_category vs profession_type
        cursor.execute("PRAGMA table_info(professionals)")
        prof_columns = {row[1]: row for row in cursor.fetchall()}
        
        if 'profession_type' in prof_columns and 'profession_category' in prof_columns:
            print("✅ Both profession_type and profession_category exist (legacy compatibility)")
        elif 'profession_type' in prof_columns and 'profession_category' not in prof_columns:
            print("Adding profession_category column...")
            cursor.execute("ALTER TABLE professionals ADD COLUMN profession_category VARCHAR(50)")
            print("✅ Added profession_category column")
        
        # Verify documents table has all required columns
        cursor.execute("PRAGMA table_info(documents)")
        doc_columns = {row[1]: row for row in cursor.fetchall()}
        
        required_doc_columns = ['professional_id', 'file_size', 'mime_type', 'is_verified']
        for col in required_doc_columns:
            if col not in doc_columns:
                print(f"❌ Missing column: documents.{col}")
            else:
                print(f"✅ documents.{col} exists")
        
        # Check if CV and PROFILE_PICTURE are valid document types
        cursor.execute("SELECT DISTINCT document_type FROM documents")
        doc_types = [row[0] for row in cursor.fetchall()]
        print(f"Current document types: {doc_types}")
        
        conn.commit()
        print("\n✅ Database schema fixed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    fix_database()
