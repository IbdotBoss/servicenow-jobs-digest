#!/bin/bash

# Simple script to run the scraper and generate HTML

echo "Running ServiceNow Jobs Scraper..."
python3 scripts/scrape_all.py

echo "Generating HTML files..."
python3 scripts/generate_archive.py

echo "✅ Done! Check docs/index.html to see the results."