#!/bin/bash

# Daily ServiceNow Jobs Digest Scraper
# Runs all scrapers and updates GitHub Pages

set -e  # Exit on error

echo "Starting daily scrape at $(date)"

# Navigate to project directory
cd /home/ubuntu/hermes-workspace/servicenow-jobs-digest

# Activate virtual environment if needed
# source venv/bin/activate

# Run the orchestrator
python3 scripts/multi_scrape.py

# Check if jobs.json was created
if [ -f "docs/data/jobs.json" ]; then
    echo "Jobs JSON created successfully"
    
    # Commit and push to GitHub Pages
    git add docs/data/jobs.json
    git commit -m "Update jobs digest - $(date)"
    git push origin main
    
    echo "GitHub Pages updated successfully"
else
    echo "Error: jobs.json not created!"
    exit 1
fi

echo "Daily scrape completed at $(date)"
