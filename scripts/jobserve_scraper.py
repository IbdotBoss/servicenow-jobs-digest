#!/usr/bin/env python3
"""JobServe Mobile Scraper — extracts SN jobs from server-rendered HTML"""
import re, html as html_mod, json, os
from urllib.request import urlopen, Request
from datetime import datetime

JS_MOBILE = "https://www.jobserve.com/gb/en/mob/JobSearch/Results?q=servicenow&l=United+Kingdom"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36'}
TODAY = datetime.now().strftime("%Y-%m-%d")
OUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobserve_jobs.json")

SN_TITLE_KW = ['servicenow', 'service-now', 'service now']

def scrape_page(page_num=1):
    url = f"{JS_MOBILE}&Page={page_num}" if page_num > 1 else JS_MOBILE
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def parse_jobs(html_text):
    jobs = []
    # Each job is in <li id="J..."> block
    blocks = re.findall(r'<li id="J([A-F0-9]+)">(.*?)</li>', html_text, re.DOTALL)
    
    for jid, block in blocks:
        pos_match = re.search(r'class="position">(.*?)</span>', block)
        if not pos_match: continue
        title = html_mod.unescape(pos_match.group(1).strip())
        
        # Only ServiceNow-specific roles
        if not any(kw in title.lower() for kw in SN_TITLE_KW): continue
        
        # Extract all spans
        spans = re.findall(r'<span>([^<]*)</span>', block)
        clean_spans = [html_mod.unescape(s.strip()) for s in spans 
                       if s.strip() and s.strip() not in ['Permanent','Contract','Any','Part Time','Temporary']
                       and not s.strip().startswith('£') and not s.strip().startswith('&#')
                       and not s.strip().startswith('+') and 'day' not in s.strip().lower()
                       and 'annum' not in s.strip().lower() and 'hour' not in s.strip().lower()
                       and s.strip() != title]
        
        location = clean_spans[0] if clean_spans else 'UK'
        salary = ''
        for s in re.findall(r'<span>([^<]*)</span>', block):
            s = html_mod.unescape(s.strip())
            if '£' in s or 'salary' in s.lower() or 'per annum' in s.lower() or 'per day' in s.lower():
                salary = s
                break
        
        # Time posted
        time_match = re.search(r'class="etime">(.*?)</span>', block)
        time_posted = html_mod.unescape(time_match.group(1).strip()) if time_match else ''
        
        # DV/SC check in title
        dv_sc = 'dv cleared' in title.lower() or 'dv-' in title.lower()
        sc = 'sc cleared' in title.lower() or 'sc eligible' in title.lower() or 'sc-' in title.lower()
        
        jobs.append({
            'title': title,
            'company': 'Extract from details',
            'location': location,
            'salary_display': salary if salary else 'Not listed',
            'date_posted': TODAY,
            'url': f"https://www.jobserve.com/gb/en/mob/job/{jid}",
            'source': 'JobServe',
            'source_type': 'agency',
            'role_type': _classify(title.lower()),
            'remote': 'remote' if 'remote' in title.lower() else ('hybrid' if 'hybrid' in title.lower() else 'onsite'),
            'employment': 'contract' if 'contract' in title.lower() or 'contract' in salary.lower() else 'permanent',
            'sc_clearance': sc or dv_sc,
            'grad_scheme': False,
            'link_status': 'live',
            'visa_sponsorship': 'sc_blocked' if (dv_sc or sc) else 'agency_unknown',
            'description': f"Posted {time_posted}" if time_posted else '',
        })
    
    return jobs

def _classify(title_lower):
    if 'architect' in title_lower: return 'architect'
    if 'developer' in title_lower or 'engineer' in title_lower: return 'developer'
    if 'consultant' in title_lower or 'specialist' in title_lower: return 'consultant'
    if 'administrator' in title_lower or 'admin' in title_lower: return 'admin'
    if 'analyst' in title_lower: return 'analyst'
    if 'manager' in title_lower or 'lead' in title_lower: return 'manager'
    return 'other'

def main():
    all_jobs = []
    for page in range(1, 5):
        try:
            html = scrape_page(page)
            jobs = parse_jobs(html)
            if not jobs: break
            all_jobs.extend(jobs)
            print(f"Page {page}: {len(jobs)} SN jobs")
        except Exception as e:
            print(f"Page {page}: {e}")
            break
    
    # Dedup
    seen = set()
    unique = []
    for j in all_jobs:
        k = j['title'].lower().strip()
        if k not in seen:
            seen.add(k)
            unique.append(j)
    
    print(f"\nTotal: {len(unique)} unique SN jobs from JobServe mobile")
    for j in unique:
        print(f"  [{j['visa_sponsorship']}] {j['title'][:70]}")
    
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    return unique

if __name__ == '__main__':
    main()
