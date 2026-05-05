#!/usr/bin/env python3
"""
ServiceNow Jobs Dashboard - Setup Wizard
"""

import os
import sys
import subprocess

def install_dependencies():
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def setup_database():
    print("🗄️  Setting up database...")
    try:
        import sqlite3
        conn = sqlite3.connect("jobs.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                date DATE NOT NULL,
                link TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                sponsorship_confirmed BOOLEAN DEFAULT 0,
                security_clearance BOOLEAN DEFAULT 0,
                tags TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON jobs(date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON jobs(source);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_location ON jobs(location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_company ON jobs(company);")
        conn.commit()
        conn.close()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_directories():
    print("📁 Creating directories...")
    dirs = [
        "docs/data",
        "scripts/scrapers"
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✓ Created {dir_path}")
    return True

def test_system():
    print("🔍 Running system tests...")
    import test_system
    return test_system.test_system()

def main():
    print("=" * 60)
    print("SERVICE NOW JOBS DASHBOARD - SETUP WIZARD")
    print("=" * 60)
    
    if not install_dependencies():
        return False
    
    if not setup_database():
        return False
    
    if not create_directories():
        return False
    
    print("\n✅ SETUP COMPLETE!")
    print("\nNext steps:")
    print("1. Test the system: python3 test_system.py")
    print("2. Run the scraper: python3 scripts/scrape_all.py")
    print("3. Start daily updates: add to crontab")
    print("4. Deploy to GitHub Pages")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)