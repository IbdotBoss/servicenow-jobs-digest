#!/usr/bin/env python3
"""
Daily cron job for ServiceNow Jobs Digest
- Runs scrapers
- Generates HTML files
- Commits to GitHub
"""

import subprocess
import sys
import datetime
import logging
from logging.handlers import RotatingFileHandler
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add rotating file handler
file_handler = RotatingFileHandler(
    'daily_scrape.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def run_command(cmd: list[str], cwd: str = None) -> bool:
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logger.error(f"Command failed: {' '.join(cmd)}\nOutput: {result.stdout}\nError: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error running command {' '.join(cmd)}: {e}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("DAILY SERVICE NOW JOBS DIGEST - CRON JOB")
    logger.info("=" * 60)
    logger.info(f"Time: {datetime.datetime.now()}")
    logger.info("Starting scraping process...")
    
    # Step 1: Run the ServiceNow aggregator (Reed + sponsor cross-reference)
    success = run_command(['python3', 'scripts/sn_aggregator.py'], cwd='/home/ubuntu/hermes-workspace/servicenow-jobs-digest')
    if not success:
        logger.error("Scraping failed! Exiting.")
        sys.exit(1)
    
    # Step 2: Commit and push to GitHub
    logger.info("Committing and pushing to GitHub...")
    try:
        # Add changes
        run_command(['git', 'add', '.'], cwd='/home/ubuntu/hermes-workspace/servicenow-jobs-digest')
        
        # Commit
        commit_msg = f"Daily digest update - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        run_command(['git', 'commit', '-m', commit_msg], cwd='/home/ubuntu/hermes-workspace/servicenow-jobs-digest')
        
        # Push
        run_command(['git', 'push', 'origin', 'main'], cwd='/home/ubuntu/hermes-workspace/servicenow-jobs-digest')
        
        logger.info("✅ Successfully pushed to GitHub")
    except Exception as e:
        logger.error(f"Git error: {e}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("CRON JOB COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()