#!/bin/bash

# ServiceNow Jobs Digest - Daily Cron
# Runs at 05:00 UK time daily

# Activate virtual environment if exists
VENV_PATH="/home/ubuntu/hermes-workspace/servicenow-jobs-digest/venv"
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
fi

# Change to project directory
cd /home/ubuntu/hermes-workspace/servicenow-jobs-digest || exit 1

# Run the multi-source scrape
echo "Starting daily scrape at $(date)"
python3 scripts/multi_scrape.py

# Generate archive HTML
if [ -f "docs/data/jobs.json" ]; then
    echo "Generating archive HTML..."
    python3 scripts/generate_archive.py
    
    echo "Updating index HTML..."
    python3 scripts/update_digest.py
    
    # Commit and push to GitHub
    git add .
    git commit -m "Daily digest update - $(date +%Y-%m-%d)"
    git push origin main
else
    echo "No jobs JSON found. Skipping HTML generation."
fi

echo "Daily cron completed at $(date)"