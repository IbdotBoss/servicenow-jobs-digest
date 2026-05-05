#!/usr/bin/env python3
"""
Initialize the ServiceNow Jobs Dashboard system
"""

import os
import subprocess
import sys

def initialize():
    print("Initializing ServiceNow Jobs Dashboard...")
    
    # Create data directory
    data_dir = "docs/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✓ Created data directory: {data_dir}")
    
    # Create empty jobs.json
    json_path = f"{data_dir}/jobs.json"
    if not os.path.exists(json_path):
        with open(json_path, "w") as f:
            f.write("[]")
        print("✓ Created empty jobs.json")
    
    # Create database
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
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠️  Database already initialized or error: {e}")
    
    # Install dependencies
    try:
        import requests
        from bs4 import BeautifulSoup
        print("✓ Dependencies already installed")
    except ImportError:
        print("Installing dependencies...")
        subprocess.run(["pip3", "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencies installed")
    
    print("\n✅ Initialization complete!")
    print("To test the system, run:")
    print("  python3 test_full_system.py")
    print("\nTo start daily updates, add to crontab:")
    print("  0 5 * * * cd /path/to/servicenow-jobs-digest && python3 daily_cron.py")

if __name__ == "__main__":
    initialize()