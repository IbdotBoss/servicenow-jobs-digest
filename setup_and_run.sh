#!/bin/bash
# ServiceNow Jobs Dashboard - Setup and Run

echo "🔧 Setting up ServiceNow Jobs Dashboard..."

# 1. Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt || { echo "❌ Failed to install dependencies"; exit 1; }

# 2. Initialize database
echo "🗄️  Initializing database..."
python3 scripts/job_model.py || { echo "❌ Failed to initialize database"; exit 1; }

# 3. Run scraper
echo "🔍 Running scraper..."
python3 scripts/scrape_all.py || { echo "❌ Scraper failed"; exit 1; }

# 4. Generate HTML
echo "🎨 Generating HTML..."
python3 scripts/generate_archive.py || { echo "❌ HTML generation failed"; exit 1; }

# 5. Set up cron (optional - run daily at 5 AM)
echo "⏰ Setting up daily cron job..."
(crontab -l 2>/dev/null | grep -v "servicenow-jobs-scraper"; echo "0 5 * * * cd $(pwd) && python3 scripts/scrape_all.py >> /var/log/jobs_scraper.log 2>&1 && python3 scripts/generate_archive.py >> /var/log/jobs_generate.log 2>&1") | crontab -

echo "✅ Setup complete!"
echo ""
echo "📁 Files created:"
echo "  - docs/index.html (dynamic dashboard)"
echo "  - docs/all-jobs.html (static archive)"
echo "  - docs/data/jobs.json (job data)"
echo ""
echo "🖥️  View locally:"
echo "  cd docs && python3 -m http.server 8000"
echo ""
echo "🌐 GitHub Pages:"
echo "  Push to main branch to deploy"
echo ""
echo "📊 Check logs:"
echo "  tail -f /var/log/jobs_scraper.log"
echo "  tail -f /var/log/jobs_generate.log"