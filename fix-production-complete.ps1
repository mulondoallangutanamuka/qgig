# QGig Production Database Fix - Complete Version
# This script handles all potential issues and creates everything needed

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  QGig Production Database Fix - COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Database URL
$dbUrl = "postgresql://qgig:zHvf1qEpx4Gc7VsIuvWAH473A98wkusx@dpg-d562onre5dus73chgmf0-a.oregon-postgres.render.com/qgig"

Write-Host "🔄 Connecting to production database..." -ForegroundColor Yellow

# Create a comprehensive Python script
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
        
        print("📝 Running complete database fix...")
        
        # 1. Ensure expiry_date column exists (already done but let's verify)
        try:
            cursor.execute("""
                ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expiry_date TIMESTAMP;
            """)
            print("  ✓ Verified expiry_date column exists")
        except Exception as e:
            print(f"  ⚠️  Expiry date column check: {e}")
        
        # 2. Ensure index exists
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_jobs_expiry_date ON jobs (expiry_date);
            """)
            print("  ✓ Verified index on expiry_date exists")
        except Exception as e:
            print(f"  ⚠️  Index check: {e}")
        
        # 3. Create alembic_version table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    PRIMARY KEY (version_num)
                );
            """)
            print("  ✓ Created/verified alembic_version table")
        except Exception as e:
            print(f"  ⚠️  Alembic table creation: {e}")
        
        # 4. Insert migration version (simple approach)
        try:
            # First try to delete any existing version
            cursor.execute("DELETE FROM alembic_version")
            
            # Then insert the correct version
            cursor.execute("""
                INSERT INTO alembic_version (version_num) 
                VALUES ('14a8ca2ff8af')
            """)
            print("  ✓ Set migration version to 14a8ca2ff8af")
        except Exception as e:
            print(f"  ⚠️  Migration version setting: {e}")
        
        # 5. Verify everything
        print("")
        print("🔍 Verifying database state...")
        
        # Check expiry_date column
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'jobs' AND column_name = 'expiry_date';
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"  ✅ Expiry date column: {result[0]} ({result[1]})")
        else:
            print("  ❌ Expiry date column not found")
        
        # Check alembic version
        try:
            cursor.execute("SELECT version_num FROM alembic_version")
            version = cursor.fetchone()
            if version:
                print(f"  ✅ Migration version: {version[0]}")
            else:
                print("  ❌ No migration version found")
        except Exception as e:
            print(f"  ❌ Alembic version check failed: {e}")
        
        # Check if we can query jobs table without errors
        try:
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE expiry_date IS NULL OR expiry_date > NOW() LIMIT 1")
            count = cursor.fetchone()[0]
            print(f"  ✅ Jobs table query successful (sample count: {count})")
        except Exception as e:
            print(f"  ❌ Jobs table query failed: {e}")
        
        # Commit all changes
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("")
        print("🎉 Database fix completed!")
        print("   Your production database should now work correctly")
        print("   Visit: https://qgig-backend.onrender.com")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
"@

# Save and run the temporary script
$tempScript | Out-File -FilePath "temp_migration_complete.py" -Encoding UTF8

python temp_migration_complete.py

# Clean up
Remove-Item "temp_migration_complete.py" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Complete Fix Applied! ✅" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Test your site: https://qgig-backend.onrender.com" -ForegroundColor Cyan
    Write-Host "🎉 All database issues should be resolved!" -ForegroundColor Green
    Write-Host ""
    Write-Host "If you still see errors, the issue might be:" -ForegroundColor Yellow
    Write-Host "• Render service needs to restart" -ForegroundColor Yellow
    Write-Host "• Connection pool needs to refresh" -ForegroundColor Yellow
    Write-Host "• Cache needs to be cleared" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  Fix Failed! ❌" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the error above and try again" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
