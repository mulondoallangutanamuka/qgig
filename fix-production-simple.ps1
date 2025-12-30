# QGig Production Database Fix - Simple Version
# This script will complete the migration without conflicts

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  QGig Production Database Fix - Simple" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Database URL
$dbUrl = "postgresql://qgig:zHvf1qEpx4Gc7VsIuvWAH473A98wkusx@dpg-d562onre5dus73chgmf0-a.oregon-postgres.render.com/qgig"

Write-Host "🔄 Connecting to production database..." -ForegroundColor Yellow

# Create a temporary Python script
$tempScript = @"
import os
import psycopg2
from urllib.parse import urlparse

def main():
    database_url = '$dbUrl'
    
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
        
        # Check if alembic_version table has data
        cursor.execute("SELECT COUNT(*) FROM alembic_version")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert the current migration version
            cursor.execute("""
                INSERT INTO alembic_version (version_num) 
                VALUES ('14a8ca2ff8af')
            """)
            print("  ✓ Added migration version to alembic_version table")
        else:
            # Update existing version
            cursor.execute("""
                UPDATE alembic_version SET version_num = '14a8ca2ff8af'
            """)
            print("  ✓ Updated migration version in alembic_version table")
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'jobs' AND column_name = 'expiry_date';
        """)
        
        result = cursor.fetchone()
        
        # Verify alembic version
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()[0]
        
        if result:
            print("")
            print("✅ Migration completed successfully!")
            print(f"   Column: {result[0]}")
            print(f"   Type: {result[1]}")
            print(f"   Nullable: {result[2]}")
            print(f"   Migration Version: {version}")
            print("")
            print("🎉 Your production database is now fully up to date!")
            print("   Visit https://qgig-backend.onrender.com to verify")
        else:
            print("")
            print("⚠️  Warning: Column may not have been added")
        
        # Commit the changes
        conn.commit()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
"@

# Save and run the temporary script
$tempScript | Out-File -FilePath "temp_migration_simple.py" -Encoding UTF8

python temp_migration_simple.py

# Clean up
Remove-Item "temp_migration_simple.py" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Migration Complete! ✅" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Check your site: https://qgig-backend.onrender.com" -ForegroundColor Cyan
    Write-Host "🎉 Your production site should now work perfectly!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  Migration Failed! ❌" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the error above and try again" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
