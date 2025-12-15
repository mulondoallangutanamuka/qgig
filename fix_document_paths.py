"""
Script to fix document file paths in database
Removes /app prefix from file_path field
"""
from app.database import SessionLocal
from app.models.document import Document

def fix_document_paths():
    db = SessionLocal()
    
    try:
        # Get all documents
        documents = db.query(Document).all()
        
        fixed_count = 0
        for doc in documents:
            # Check if path starts with /app/static
            if doc.file_path and doc.file_path.startswith('/app/static'):
                old_path = doc.file_path
                # Remove /app prefix
                doc.file_path = doc.file_path.replace('/app/static', '/static')
                print(f"Fixed: {old_path} -> {doc.file_path}")
                fixed_count += 1
            elif doc.file_path and doc.file_path.startswith('app/static'):
                old_path = doc.file_path
                # Remove app/ prefix
                doc.file_path = '/' + doc.file_path.replace('app/static', 'static')
                print(f"Fixed: {old_path} -> {doc.file_path}")
                fixed_count += 1
        
        if fixed_count > 0:
            db.commit()
            print(f"\n✅ Fixed {fixed_count} document paths")
        else:
            print("\n✅ No paths needed fixing")
        
        # Show all current paths
        print("\n=== Current Document Paths ===")
        documents = db.query(Document).all()
        for doc in documents:
            print(f"ID {doc.id}: {doc.file_path}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_document_paths()
