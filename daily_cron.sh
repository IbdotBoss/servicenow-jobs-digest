#!/bin/bash

# ServiceNow Jobs Digest - Daily Cron Script
# Runs daily at 05:00 UK time to scrape jobs and update GitHub Pages

# Activate virtual environment (if applicable)
# source /path/to/venv/bin/activate

# Set project directory
cd /home/ubuntu/hermes-workspace/servicenow-jobs-digest

# Run multi-source scrape
echo "Running multi-source scrape..."
python3 scripts/multi_scrape.py

# Check if jobs.json was created
if [ -f "docs/data/jobs.json" ]; then
    echo "Jobs JSON created. Generating archive..."
    python3 scripts/generate_archive.py
    
    echo "Updating index HTML..."
    python3 scripts/update_digest.py
    
    echo "Committing and pushing to GitHub..."
    git add .
    git commit -m "Daily digest update - $(date +%Y-%m-%d)"
    git push origin main
else:
    echo "No jobs JSON created. Something went wrong."
fi