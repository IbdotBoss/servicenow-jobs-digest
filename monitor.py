#!/usr/bin/env python3
"""Monitoring script for ServiceNow Jobs Digest"""

import sys
import os
import subprocess
import smtplib
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Ensure scripts directory is in path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import sqlite3
try:
    from job_model import Job
except ImportError as e:
    print(f"Failed to import Job from job_model: {e}")
    print("Trying alternative import...")
    # Try to import from the scripts directory directly
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from scripts.job_model import Job
    except ImportError as e2:
        print(f"Failed to import Job: {e2}")
        raise

# Configuration
ADMIN_EMAILS = ["admin@example.com", "stage@example.com"]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "your-email@gmail.com"
EMAIL_PASS = "your-password"

def send_alert(subject, body, recipients):
    """Send email alert"""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = ",".join(recipients)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, recipients, msg.as_string())
        server.quit()
        print(f"Alert email sent to {recipients}")
    except Exception as e:
        print(f"Failed to send alert email: {e}")

def check_scraper(scraper_name, command):
    """Run a scraper and check its exit code"""
    print(f"Running {scraper_name}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            error_msg = f"{scraper_name} failed with exit code {result.returncode}\\n\\nError:\\n{result.stderr}"
            print(error_msg)
            send_alert(
                f"[ServiceNow Jobs] {scraper_name} FAILED",
                error_msg,
                ADMIN_EMAILS
            )
            return False
        else:
            print(f"{scraper_name} completed successfully")
            return True
    except subprocess.TimeoutExpired:
        error_msg = f"{scraper_name} timed out after 300 seconds"
        print(error_msg)
        send_alert(
            f"[ServiceNow Jobs] {scraper_name} TIMEOUT",
            error_msg,
            ADMIN_EMAILS
        )
        return False
    except Exception as e:
        error_msg = f"{scraper_name} raised an exception: {str(e)}"
        print(error_msg)
        send_alert(
            f"[ServiceNow Jobs] {scraper_name} EXCEPTION",
            error_msg,
            ADMIN_EMAILS
        )
        return False

def check_database():
    """Check if the database has been updated recently"""
    try:
        conn = sqlite3.connect("jobs.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE timestamp > datetime('now', '-1 day')")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        if count == 0:
            error_msg = "No new jobs added to database in the last 24 hours"
            print(error_msg)
            send_alert(
                "[ServiceNow Jobs] DATABASE ALERT",
                error_msg,
                ADMIN_EMAILS
            )
            return False
        else:
            print(f"Database has {count} new jobs in the last 24 hours")
            return True
    except Exception as e:
        error_msg = f"Error checking database: {str(e)}"
        print(error_msg)
        send_alert(
            "[ServiceNow Jobs] DATABASE CHECK FAILED",
            error_msg,
            ADMIN_EMAILS
        )
        return False

def main():
    print("=" * 60)
    print("SERVICE-now JOBS DIGEST MONITORING")
    print("=" * 60)
    
    # List of scrapers to check (name, command)
    scrapers = [
        ("Hunt UK", "python scripts/scrapers/hunt_uk_playwright_scraper.py"),
        ("CWJobs", "python scripts/scrapers/cwjobs_scraper.py"),
        ("Technojobs", "python scripts/scrapers/technojobs_scraper.py"),
        ("Prospects", "python scripts/scrapers/prospects_scraper.py"),
        ("Gradcracker", "python scripts/scrapers/gradcracker_scraper.py"),
        ("Milkround", "python scripts/scrapers/milkround_scraper.py"),
        ("CareerJet", "python scripts/scrapers/careerjet_scraper.py"),
        ("Adzuna", "python scripts/scrapers/adzuna_scraper.py"),
    ]
    
    # Run all scrapers
    all_passed = True
    for scraper_name, command in scrapers:
        if not check_scraper(scraper_name, command):
            all_passed = False
    
    # Check database
    if not check_database():
        all_passed = False
    
    if all_passed:
        print("\n✓ All systems operational!")
    else:
        print("\n✗ Some checks failed. Please review alerts.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
