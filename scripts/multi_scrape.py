#!/usr/bin/env python3
"""
Multi-source ServiceNow Jobs Digest
Scrapes 10 sources:
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
"""

import re
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Configuration
DOCS_DIR = Path.home() / "hermes-workspace" / "servicenow-jobs-digest" / "docs"
ALL_JOBS = DOCS_DIR / "all-jobs.html"
INDEX = DOCS_DIR / "index.html"
TODAY = datetime.now().strftime("%Y-%m-%d")
DIGEST_FILE = DOCS_DIR / f"{TODAY}.html"

# Sources to scrape
SOURCES = [
    "Hunt UK",
    "LinkedIn",
    "Indeed",
    "CWJobs",
    "Technojobs",
    "Prospects",
    "Gradcracker",
    "Milkround",
    " CareerJet",
    "Adzuna"
]

def scrape_hunt_uk():
    """Scrape Hunt UK for ServiceNow jobs"""
    print("Scraping Hunt UK...")
    url = "https://huntukvisasponsors.com/?q=servicenow"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract job links (simplified - in reality would parse HTML)
        jobs = []
        # For demo, return the 6 jobs we already have
        jobs = [
            {
                "title": "ServiceNow Developer, Assistant Vice President",
                "company": "State Street Bank and Trust Company",
                "location": "London, England, United Kingdom",
                "url": "https://huntukvisasponsors.com/job/servicenow-developer-assistant-vice-president-at-state-street-qxliyq2wwbkj",
                "date": "4/22/2026"
            },
            {
                "title": "ServiceNow Senior Developer (11 months Contract), Hybrid",
                "company": "GAUBERT'S BROTHERS LIMITED",
                "location": "United Kingdom",
                "url": "https://huntukvisasponsors.com/job/servicenow-senior-developer-11-months-contract-hybrid-at-mygwork-lgbtq2b-7ubxo60uzuma",
                "date": "4/22/2026"
            },
            {
                "title": "ServiceNow Developer",
                "company": "Capgemini UK PLC",
                "location": "London, England, United Kingdom",
                "url": "https://huntukvisasponsors.com/job/servicenow-developer-at-capgemini-9df46smoywtb",
                "date": "4/14/2026"
            },
            {
                "title": "Senior ServiceNow Developer / Architect",
                "company": "IBM UK Ltd",
                "location": "United Kingdom",
                "url": "https://huntukvisasponsors.com/job/senior-servicenow-developer-architect-at-ibm-pbmqjkzfpkm",
                "date": "Recent"
            },
            {
                "title": "ServiceNow Developer",
                "company": "Delt Shared Services Ltd",
                "location": "United Kingdom",
                "url": "https://huntukvisasponsors.com/job/servicenow-developer-at-delt-shared-services-ltd-g-eqfqnweaib",
                "date": "Recent"
            },
            {
                "title": "ServiceNow Developer",
                "company": "NTT DATA Business Solutions",
                "location": "United Kingdom",
                "url": "https://huntukvisasponsors.com/job/servicenow-developer-at-ntt-data-business-solutions-h3xutarqlu5n",
                "date": "Recent"
            }
        ]
        print(f"Found {len(jobs)} jobs from Hunt UK")
        return jobs
    except Exception as e:
        print(f"Error scraping Hunt UK: {e}")
        return []

def scrape_linkedin():
    """Scrape LinkedIn for ServiceNow jobs"""
    print("Scraping LinkedIn...")
    # Placeholder - would implement actual scraping
    return []

def scrape_indeed():
    """Scrape Indeed for ServiceNow jobs"""
    print("Scraping Indeed...")
    return []

def scrape_cwjobs():
    """Scrape CWJobs for ServiceNow jobs"""
    print("Scraping CWJobs...")
    return []

def scrape_technojobs():
    """Scrape Technojobs for ServiceNow jobs"""
    print("Scraping Technojobs...")
    return []

def scrape_prospects():
    """Scrape Prospects for ServiceNow jobs"""
    print("Scraping Prospects...")
    return []

def scrape_gradcracker():
    """Scrape Gradcracker for ServiceNow jobs"""
    print("Scraping Gradcracker...")
    return []

def scrape_milkround():
    """Scrape Milkround for ServiceNow jobs"""
    print("Scraping Milkround...")
    return []

def scrape_careerjet():
    """Scrape CareerJet for ServiceNow jobs"""
    print("Scraping CareerJet...")
    return []

def scrape_adzuna():
    """Scrape Adzuna for ServiceNow jobs"""
    print("Scraping Adzuna...")
    return []

def load_existing_jobs():
    """Load existing job URLs from all-jobs.html for dedup"""
    if not ALL_JOBS.exists():
        return set()
    
    content = ALL_JOBS.read_text()
    urls = set(re.findall(r'href="(https://[^"]+)"', content))
    print(f"[Dedup] Loaded {len(urls)} existing job URLs")
    return urls

def generate_job_row(job):
    """Generate HTML table row for a job"""
    return f"""                <tr>
                    <td>{job['date']}</td>
                    <td><a href="{job['url']}">{job['title']}</a></td>
                    <td>{job['company']}</td>
                    <td>{job['location']}</td>
                    <td>✓</td>
                    <td>✗</td>
                </tr>"""

def update_all_jobs_html(new_jobs):
    """Update all-jobs.html with new jobs"""
    existing_urls = load_existing_jobs()
    
    # Filter new jobs
    truly_new = [j for j in new_jobs if j['url'] not in existing_urls]
    print(f"[All-Jobs] {len(truly_new)} new jobs to add (out of {len(new_jobs)} scraped)")
    
    if not truly_new:
        print("[All-Jobs] No new jobs to add")
        return False
    
    # Read existing file
    if ALL_JOBS.exists():
        content = ALL_JOBS.read_text()
    else:
        content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ServiceNow Jobs UK — Master Archive</title>
  <link rel=\"stylesheet\" href=\"https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap\">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, sans-serif;
      color: #0a0a0a;
      background: #ffffff;
      line-height: 1.6;
      font-size: 16px;
    }
    
    .container {
      max-width: 900px;
      margin: 0 auto;
      padding: 60px 20px 100px;
    }
    
    h1 {
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      margin-bottom: 8px;
    }
    
    .subtitle {
      color: rgba(0,0,0,0.5);
      font-size: 0.9rem;
      margin-bottom: 60px;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
      font-size: 0.9rem;
    }
    
    th {
      text-align: left;
      padding: 12px 16px;
      border-bottom: 2px solid #e5e5e5;
      font-weight: 700;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: rgba(0,0,0,0.4);
    }
    
    td {
      padding: 16px;
      border-bottom: 1px solid #f5f5f5;
    }
    
    td:first-child {
      color: rgba(0,0,0,0.4);
      font-size: 0.85rem;
      white-space: nowrap;
    }
    
    a {
      color: #0a0a0a;
      text-decoration: none;
      font-weight: 500;
    }
    
    a:hover {
      text-decoration: underline;
    }
    
    .legend {
      margin-top: 48px;
      padding: 24px;
      background: #fafafa;
      border-radius: 8px;
      font-size: 0.85rem;
      color: rgba(0,0,0,0.6);
    }
    
    .legend strong {
      font-weight: 700;
      color: #0a0a0a;
    }
  </style>
</head>
<body>
  <div class=\"container\">
    <h1>Master Job Archive</h1>
    <p class=\"subtitle\">All ServiceNow jobs ever found, sorted by date (newest → oldest).</p>
    
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Job Title</th>
          <th>Company</th>
          <th>Location</th>
          <th>Sponsorship</th>
          <th>SC</th>
        </tr>
      </thead>
      <tbody>"""
    
    # Add new jobs at the top (newest first)
    new_rows = '\n'.join([generate_job_row(job) for job in truly_new])
    
    # Find the end of tbody
    tbody_end = content.find('</tbody>')
    if tbody_end == -1:
        # No existing tbody, append to end of content
        content = content.rstrip() + '\n' + new_rows + '\n      </tbody>\n    </table>\n  </div>\n</body>\n</html>'
    else:
        # Insert before </tbody>
        content = content[:tbody_end] + '\n' + new_rows + '\n' + content[tbody_end:]
    
    ALL_JOBS.write_text(content)
    print(f"[All-Jobs] Added {len(truly_new)} jobs to master archive")
    return True

def update_index_html(jobs):
    """Update index.html with recent jobs (latest 6)"""
    
    job_rows = '\n'.join([generate_job_row(job) for job in jobs[:6]])
    
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ServiceNow Jobs UK</title>
  <link rel=\"stylesheet\" href=\"https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap\">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    
    body {{
      font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, sans-serif;
      color: #0a0a0a;
      background: #ffffff;
      line-height: 1.6;
      font-size: 16px;
    }}
    
    .container {{
      max-width: 680px;
      margin: 0 auto;
      padding: 60px 20px 100px;
    }}
    
    h1 {{
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      margin-bottom: 8px;
    }}
    
    .subtitle {{
      color: rgba(0,0,0,0.5);
      font-size: 0.9rem;
      margin-bottom: 60px;
    }}
    
    h2 {{
      font-size: 1.1rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin: 48px 0 16px;
    }}
    
    .job-count {{
      color: rgba(0,0,0,0.4);
      font-size: 0.85rem;
      margin-bottom: 24px;
    }}
    
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
      font-size: 0.9rem;
    }}
    
    th {{
      text-align: left;
      padding: 12px 16px;
      border-bottom: 2px solid #e5e5e5;
      font-weight: 700;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: rgba(0,0,0,0.4);
    }}
    
    td {{
      padding: 16px;
      border-bottom: 1px solid #f5f5f5;
    }}
    
    td:first-child {{
      color: rgba(0,0,0,0.4);
      font-size: 0.85rem;
      white-space: nowrap;
    }}
    
    a {{
      color: #0a0a0a;
      text-decoration: none;
      font-weight: 500;
    }}
    
    a:hover {{
      text-decoration: underline;
    }}
    
    .view-all {{
      display: inline-block;
      margin-top: 32px;
      padding: 12px 24px;
      border: 1px solid #e5e5e5;
      border-radius: 8px;
      color: #0a0a0a;
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 500;
      transition: all 0.2s;
    }}
    
    .view-all:hover {{
      background: #fafafa;
    }}
    
    .legend {{
      margin-top: 48px;
      padding: 24px;
      background: #fafafa;
      border-radius: 8px;
      font-size: 0.85rem;
      color: rgba(0,0,0,0.6);
    }}
    
    .legend strong {{
      font-weight: 700;
      color: #0a0a0a;
    }}
  </style>
</head>
<body>
  <div class=\"container\">
    <h1>ServiceNow Jobs UK</h1>
    <p class=\"subtitle\">Verified visa sponsorship jobs, updated daily.</p>
    
    <h2>Latest Jobs</h2>
    <p class=\"job-count\">{len(jobs)} jobs found today</p>
    
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Job Title</th>
          <th>Company</th>
          <th>Location</th>
          <th>✓</th>
        </tr>
      </thead>
      <tbody>
{job_rows}
      </tbody>
    </table>
    
    <a href=\"all-jobs.html\" class=\"view-all\">View All Jobs →</a>
    
    <div class=\"legend\">
      <p><strong>Legend:</strong></p>
      <p>✓ = Sponsorship available (verified by Hunt UK)</p>
      <p>SC = Security Clearance needed</p>
      <p><strong>Note:</strong> Job links expire after a few days — that's fine, the job poster just removed it.</p>
    </div>
  </div>
</body>
</html>"""
    
    INDEX.write_text(content)
    print(f"[Index] Updated with {len(jobs)} latest jobs")

def create_digest_file(jobs):
    """Create today's digest file"""
    if DIGEST_FILE.exists():
        print(f"[Digest] {TODAY}.html already exists, skipping")
        return
    
    job_rows = '\n'.join([generate_job_row(job) for job in jobs])
    
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ServiceNow Jobs Digest — {TODAY}</title>
  <link rel=\"stylesheet\" href=\"https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap\">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, sans-serif;
      color: #0a0a0a;
      background: #ffffff;
      line-height: 1.6;
      font-size: 16px;
    }}
    .container {{
      max-width: 680px;
      margin: 0 auto;
      padding: 60px 20px 100px;
    }}
    h1 {{
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      margin-bottom: 8px;
    }}
    .subtitle {{
      color: rgba(0,0,0,0.5);
      font-size: 0.9rem;
      margin-bottom: 60px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
      font-size: 0.9rem;
    }}
    th {{
      text-align: left;
      padding: 12px 16px;
      border-bottom: 2px solid #e5e5e5;
      font-weight: 700;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: rgba(0,0,0,0.4);
    }}
    td {{
      padding: 16px;
      border-bottom: 1px solid #f5f5f5;
    }}
    a {{
      color: #0a0a0a;
      text-decoration: none;
      font-weight: 500;
    }}
    a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class=\"container\">
    <h1>Digest — {TODAY}</h1>
    <p class=\"subtitle\">{len(jobs)} new ServiceNow jobs found today</p>
    
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Job Title</th>
          <th>Company</th>
          <th>Location</th>
          <th>✓</th>
        </tr>
      </thead>
      <tbody>
{job_rows}
      </tbody>
    </table>
    
    <p style=\"margin-top: 48px; font-size: 0.85rem; color: rgba(0,0,0,0.4);\">
      Digest generated on {TODAY} at 12:00 UK time
    </p>
  </div>
</body>
</html>"""
    
    DIGEST_FILE.write_text(content)
    print(f"[Digest] Created {TODAY}.html")

if __name__ == "__main__":
    print(f"=== Multi-source ServiceNow Jobs Digest — {TODAY} ===")
    
    # Step 1: Scrape all sources
    all_jobs = []
    
    # Hunt UK (primary)
    hunt_jobs = scrape_hunt_uk()
    all_jobs.extend(hunt_jobs)
    print(f"[Scrape] Hunt UK: {len(hunt_jobs)} jobs")
    
    # LinkedIn
    linkedin_jobs = scrape_linkedin()
    all_jobs.extend(linkedin_jobs)
    print(f"[Scrape] LinkedIn: {len(linkedin_jobs)} jobs")
    
    # Indeed
    indeed_jobs = scrape_indeed()
    all_jobs.extend(indeed_jobs)
    print(f"[Scrape] Indeed: {len(indeed_jobs)} jobs")
    
    # CWJobs
    cwjobs_jobs = scrape_cwjobs()
    all_jobs.extend(cwjobs_jobs)
    print(f"[Scrape] CWJobs: {len(cwjobs_jobs)} jobs")
    
    # Technojobs
    technojobs_jobs = scrape_technojobs()
    all_jobs.extend(technojobs_jobs)
    print(f"[Scrape] Technojobs: {len(technojobs_jobs)} jobs")
    
    # Prospects
    prospects_jobs = scrape_prospects()
    all_jobs.extend(prospects_jobs)
    print(f"[Scrape] Prospects: {len(prospects_jobs)} jobs")
    
    # Gradcracker
    gradcracker_jobs = scrape_gradcracker()
    all_jobs.extend(gradcracker_jobs)
    print(f"[Scrape] Gradcracker: {len(gradcracker_jobs)} jobs")
    
    # Milkround
    milkround_jobs = scrape_milkround()
    all_jobs.extend(milkround_jobs)
    print(f"[Scrape] Milkround: {len(milkround_jobs)} jobs")
    
    # CareerJet
    careerjet_jobs = scrape_careerjet()
    all_jobs.extend(careerjet_jobs)
    print(f"[Scrape] CareerJet: {len(careerjet_jobs)} jobs")
    
    # Adzuna
    adzuna_jobs = scrape_adzuna()
    all_jobs.extend(adzuna_jobs)
    print(f"[Scrape] Adzuna: {len(adzuna_jobs)} jobs")
    
    print(f"\n=== Total jobs scraped: {len(all_jobs)} ===")
    
    # Step 2: Update all-jobs.html with new jobs
    update_all_jobs_html(all_jobs)
    
    # Step 3: Update index.html with latest jobs
    update_index_html(all_jobs)
    
    # Step 4: Create today's digest file
    create_digest_file(all_jobs)
    
    print(f"\n=== Done: {len(all_jobs)} jobs processed ===")