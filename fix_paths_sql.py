"""
Fix document paths using raw SQL to avoid enum issues
"""
from app.database import SessionLocal
from sqlalchemy import text

def fix_paths():
    db = SessionLocal()
    
    try:
        # Get all documents with their current paths
        result = db.execute(text("SELECT id, file_path FROM documents"))
        documents = result.fetchall()
        
        print("=== Current Document Paths ===")
        for doc_id, file_path in documents:
            print(f"ID {doc_id}: {file_path}")
        
        # Fix paths that start with /app/static or app/static or app\static
        fixed_count = 0
        
        # Fix /app/static -> /static
        result = db.execute(
            text("UPDATE documents SET file_path = REPLACE(file_path, '/app/static', '/static') WHERE file_path LIKE '/app/static%'")
        )
        fixed_count += result.rowcount
        
        # Fix app\static -> /static (Windows backslashes)
        result = db.execute(
            text("UPDATE documents SET file_path = REPLACE(REPLACE(file_path, '\\', '/'), 'app/static', '/static') WHERE file_path LIKE 'app%static%'")
        )
        fixed_count += result.rowcount
        
        # Fix app/static -> /static (without leading slash)
        result = db.execute(
            text("UPDATE documents SET file_path = '/' || REPLACE(file_path, 'app/static', 'static') WHERE file_path LIKE 'app/static%' AND file_path NOT LIKE '/%'")
        )
        fixed_count += result.rowcount
        
        db.commit()
        
        print(f"\n✅ Fixed {fixed_count} document paths")
        
        # Show updated paths
        result = db.execute(text("SELECT id, file_path FROM documents"))
        documents = result.fetchall()
        
        print("\n=== Updated Document Paths ===")
        for doc_id, file_path in documents:
            print(f"ID {doc_id}: {file_path}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_paths()
