# ServiceNow Jobs UK - Dynamic Dashboard

A dynamic, multi-source job aggregator for ServiceNow positions in the UK with visa sponsorship filtering.

## 🚀 Features

- **Real-time Filtering**: Search, filter by location, company, source, sponsorship, and remote work
- **Sorting & Grouping**: Sort by date, company, location; group by company, location, source, or tags
- **Two View Modes**: Grid view for quick scanning, list view for detailed review
- **Mobile Responsive**: Works seamlessly on all devices
- **Daily Updates**: Automated scraping and deployment
- **Minimalist Design**: Typography-focused interface using Satoshi font, monochrome palette, generous whitespace

## 📋 Architecture

### **Backend (Python)**
- **SQLite Database**: Stores all scraped jobs with deduplication
- **Modular Scrapers**: Individual scraper modules for each source
- **Orchestrator**: Coordinates scraping, data processing, and HTML generation
- **Cron Job**: Daily automation via Linux crontab

### **Frontend (HTML/JS/CSS)**
- **Dynamic Dashboard**: Client-side filtering, sorting, grouping
- **Static Archive**: Fallback HTML for no-JS environments
- **Minimalist Design**: Clean typography, generous whitespace, monochrome palette

## 📦 Files

```
servicenow-jobs-digest/
├── scripts/
│   ├── scrape_all.py        # Main orchestrator
│   ├── generate_archive.py   # Static HTML generator
│   ├── job_model.py         # Data model and utilities
│   └── scrapers/            # Individual scraper modules
├── docs/                   # GitHub Pages site
│   ├── index.html          # Dynamic dashboard
│   ├── styles.css          # Minimalist CSS
│   ├── jobs.js             # Filtering/sorting logic
│   ├── data/               # JSON data storage
│   └── all-jobs.html       # Static archive
└── requirements.txt        # Python dependencies
```

## 🔧 Setup Instructions

### Prerequisites
- Python 3.8+
- pip3
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/IbdotBoss/servicenow-jobs-digest.git
   cd servicenow-jobs-digest
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Set up database (automatic):
   ```bash
   python3 scripts/scrape_all.py
   ```

### Running Locally

1. Run the scraper:
   ```bash
   python3 scripts/scrape_all.py
   ```

2. Generate archive:
   ```bash
   python3 scripts/generate_archive.py
   ```

3. Start a local web server:
   ```bash
   cd docs
   python3 -m http.server 8000
   ```

4. Open in browser: `http://localhost:8000`

### Deployment to GitHub Pages

The site is already configured for GitHub Pages. To update:

1. Run the scraper and generate archive
2. Commit and push to main branch
3. GitHub Pages will automatically rebuild

### Cron Job Setup

To run daily at 05:00 UK time:

```bash
crontab -e
```

Add this line:
```
0 5 * * * cd /path/to/servicenow-jobs-digest && /usr/bin/python3 scripts/scrape_all.py >> /var/log/jobs_scraper.log 2>&1 && /usr/bin/python3 scripts/generate_archive.py >> /var/log/jobs_generate.log 2>&1
```

## 🧠 Technical Details

### **Database Schema**
```sql
CREATE TABLE jobs (
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
```

### **Scrapers Implemented**
- Hunt UK Visa Sponsors
- Indeed UK
- LinkedIn Jobs (planned)
- CWJobs (planned)
- Technojobs (planned)
- Prospects (planned)
- Gradcracker (planned)
- Milkround (planned)
- CareerJet (planned)
- Adzuna (planned)

### **Design Principles**

- **Minimalism**: Clean typography, generous whitespace, monochrome palette
- **Performance**: No heavy frameworks, vanilla JavaScript for fast loading
- **Accessibility**: Semantic HTML, proper contrast ratios
- **Responsive**: Works on mobile, tablet, and desktop

## 🚦 Roadmap

- [x] Dynamic filtering/sorting/grouping frontend
- [x] SQLite database for job storage
- [x] Modular scraper framework
- [ ] Implement remaining scrapers (7/10)
- [ ] Set up daily cron automation
- [ ] Add email alerts for new jobs
- [ ] Implement salary parsing
- [ ] Add user accounts (optional)

## 📄 License

MIT License. Copyright © 2026 Stage & Mr Faajii.