# QGig Production Database Fix - PowerShell Script
# This script will add the missing expiry_date column to your production database

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  QGig Production Database Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if psycopg2 is installed
try {
    $result = python -c "import psycopg2" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing psycopg2..." -ForegroundColor Yellow
        pip install psycopg2-binary
        Write-Host "✅ psycopg2 installed!" -ForegroundColor Green
    }
} catch {
    Write-Host "Installing psycopg2..." -ForegroundColor Yellow
    pip install psycopg2-binary
    Write-Host "✅ psycopg2 installed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Please provide your Render PostgreSQL connection string:" -ForegroundColor Cyan
Write-Host "(Go to Render Dashboard → Database → Connections → Copy External Database URL)" -ForegroundColor Gray
Write-Host ""

$dbUrl = Read-Host "Enter DATABASE_URL"

if ([string]::IsNullOrWhiteSpace($dbUrl)) {
    Write-Host "❌ No database URL provided. Exiting." -ForegroundColor Red
    exit 1
}

Write-Host ""
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
        
        # Add the expiry_date column
        cursor.execute("""
            ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expiry_date TIMESTAMP;
        """)
        print("  ✓ Added expiry_date column")
        
        # Create index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_jobs_expiry_date ON jobs (expiry_date);
        """)
        print("  ✓ Created index on expiry_date")
        
        # Update alembic version
        cursor.execute("""
            UPDATE alembic_version SET version_num = '14a8ca2ff8af' 
            WHERE version_num IS NOT NULL;
        """)
        print("  ✓ Updated migration version")
        
        # Commit the changes
        conn.commit()
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'jobs' AND column_name = 'expiry_date';
        """)
        
        result = cursor.fetchone()
        
        if result:
            print("")
            print("✅ Migration completed successfully!")
            print(f"   Column: {result[0]}")
            print(f"   Type: {result[1]}")
            print(f"   Nullable: {result[2]}")
            print("")
            print("🎉 Your production database is now up to date!")
            print("   Visit https://qgig-backend.onrender.com to verify")
        else:
            print("")
            print("⚠️  Warning: Column may not have been added")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
"@

# Save and run the temporary script
$tempScript | Out-File -FilePath "temp_migration.py" -Encoding UTF8

python temp_migration.py

# Clean up
Remove-Item "temp_migration.py" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Migration Complete! ✅" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Check your site: https://qgig-backend.onrender.com" -ForegroundColor Cyan
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
