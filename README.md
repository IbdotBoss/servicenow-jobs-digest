# ServiceNow Jobs UK - Daily Digest

A dynamic, multi-source job aggregator for ServiceNow positions in the UK with visa sponsorship filtering.

## Features

- **Multi-source scraping**: Fetches jobs from 10+ sources including Hunt UK, LinkedIn, Indeed, and more
- **Real-time filtering**: Search, filter by location, company, source, sponsorship, and remote work
- **Sorting & grouping**: Sort by date, company, location; group by company, location, source, or tags
- **Two view modes**: Grid view for quick scanning, list view for detailed review
- **Daily updates**: Cron job runs daily at 05:00 UK to fetch fresh jobs
- **Minimalist design**: Clean, typography-focused interface using Satoshi font
- **Mobile responsive**: Works on all devices

## Architecture

```
servicenow-jobs-digest/
├── scripts/
│   ├── scrapers/          # Individual scrapers for each source
│   │   ├── hunt_uk_scraper.py
│   │   ├── linkedin_scraper.py
│   │   ├── indeed_scraper.py
│   │   └── ... (others)
│   ├── multi_scrape.py    # Orchestrates all scrapers
│   ├── update_digest.py    # Updates HTML files from scraped data
│   └── job_model.py        # Data model and utilities
├── docs/                  # GitHub Pages site
│   ├── index.html         # Main dashboard with filtering
│   ├── styles.css         # Minimalist CSS
│   ├── jobs.js            # Interactive JavaScript
│   ├── data/              # JSON data storage
│   │   └── jobs.json      # Scraped job data
│   ├── all-jobs.html      # Master archive (static backup)
│   └── ... (other static files)
└── README.md
```

## How It Works

1. **Scraping**: The `multi_scrape.py` script runs daily via cron and calls all scrapers in the `scrapers/` directory.
2. **Data Processing**: Each scraper returns standardized `Job` objects with consistent fields.
3. **Deduplication**: Jobs are deduplicated based on URL or hash to avoid duplicates from multiple sources.
4. **Storage**: Cleaned job data is saved as JSON in `docs/data/jobs.json`.
5. **Frontend**: The `index.html` page loads this JSON and provides interactive filtering, sorting, and grouping.

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip3
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/IbdotBoss/servicenow-jobs-digest.git
cd servicenow-jobs-digest

# Install dependencies
pip3 install requests beautifulsoup4

# Set up cron job (runs daily at 05:00 UK)
0 5 * * * cd /path/to/servicenow-jobs-digest && /usr/bin/python3 scripts/multi_scrape.py && /usr/bin/python3 scripts/update_digest.py
```

### Development
```bash
# Install dependencies
pip3 install -r requirements.txt

# Run scrapers manually
python3 scripts/multi_scrape.py

# Update HTML files
python3 scripts/update_digest.py
```

## Data Sources

Currently supported job sites:
1. Hunt UK (primary)
2. LinkedIn
3. Indeed
4. CWJobs
5. Technojobs
6. Prospects
7. Gradcracker
8. Milkround
9. CareerJet
10. Adzuna

## Design Principles

- **Minimalist**: Clean typography, generous whitespace, monochrome palette
- **Fast**: No heavy frameworks, vanilla JavaScript for performance
- **Accessible**: Semantic HTML, proper contrast ratios
- **Responsive**: Works on mobile, tablet, and desktop

## License

MIT License. Copyright © 2026 Stage & Mr Faajii.