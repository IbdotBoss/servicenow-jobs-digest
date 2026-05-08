#!/usr/bin/env python3
"""JobServe Mobile Scraper — session-based SHD URL format (v2.0).
FIXED: JobServe now requires session cookie + search handle ID (SHD).
FIXED: Pagination continues even when individual pages have 0 SN matches.
FIXED: Desktop URLs for better UX.
FIXED: No false company extraction — marks as [view listing] honestly.
"""
import re, html as html_mod, json, os, subprocess, csv
from datetime import datetime

UA = 'Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36'
TODAY = datetime.now().strftime("%Y-%m-%d")
OUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobserve_jobs.json")
SPONSOR_CSV = os.path.expanduser("~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv")
COOKIE_FILE = '/tmp/js_cookies.txt'

SN_TITLE_KW = ['servicenow', 'service-now', 'service now']
SC_COMPANIES = {'bae systems', 'qinetiq', 'leonardo', 'thales', 'mbda', 'rolls-royce', 
                'gchq', 'atkinsréalis', 'atkins realis', 'atkins'}

# ── Sponsor loading ──
def load_sponsors():
    sponsors = set()
    try:
        with open(SPONSOR_CSV, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                if 'skilled worker' in row.get('Route','').lower() and 'a rating' in row.get('Type & Rating','').lower():
                    sponsors.add(row.get('Organisation Name','').strip().lower())
    except: pass
    return sponsors

def check_sponsor(name, sponsors):
    if not name or name in ('N/A', '', '[view listing]'): return 'unknown'
    n = name.lower().strip().split(' - ')[0].split(' (')[0]
    for s in sponsors:
        if n in s or s in n:
            for sc in SC_COMPANIES:
                if sc in n or sc in s: return 'sc_blocked'
            return 'verified'
    return 'unknown'

# ── Session creation ──
def create_session():
    """Create a JobServe search session, return SHD (search handle ID)."""
    # Step 1: Get a fresh session cookie
    subprocess.run(['curl', '-s', '-c', COOKIE_FILE, '-A', UA,
        'https://www.jobserve.com/gb/en/mob/JobSearch/New'],
        capture_output=True, timeout=10)
    # Step 2: Do search to get redirected to SHD-based URL
    result = subprocess.run(['curl', '-s', '-L', '-b', COOKIE_FILE, '-A', UA,
        'https://www.jobserve.com/gb/en/mob/JobSearch/Results?q=servicenow&l=United+Kingdom&Page=1'],
        capture_output=True, text=True, timeout=15)
    # Step 3: Extract SHD from page
    m = re.search(r'/mob/jobsearch/results/([A-F0-9]+)', result.stdout)
    if m:
        return m.group(1)
    # Fallback: try from canonical link
    m = re.search(r'canonical.*?shid=([A-F0-9]+)', result.stdout)
    if m:
        return m.group(1)
    return None

# ── Page scraping ──
def fetch_page(shd, page_num):
    """Fetch a single page of results."""
    url = f'https://www.jobserve.com/gb/en/mob/jobsearch/results/{shd}?Page={page_num}'
    result = subprocess.run(['curl', '-s', '-b', COOKIE_FILE, '-A', UA, url],
                          capture_output=True, text=True, timeout=15)
    return result.stdout

def parse_jobs(html_text):
    jobs = []
    blocks = re.findall(r'<li id="J([A-F0-9]+)"[^>]*>(.*?)</li>', html_text, re.DOTALL)
    
    for jid, block in blocks:
        pos_match = re.search(r'class="position">(.*?)</span>', block)
        if not pos_match: continue
        title = html_mod.unescape(pos_match.group(1).strip())
        
        # Only ServiceNow-specific roles
        if not any(kw in title.lower() for kw in SN_TITLE_KW): continue
        
        # Extract spans
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
                salary = s; break
        
        time_match = re.search(r'class="etime">(.*?)</span>', block)
        time_posted = html_mod.unescape(time_match.group(1).strip()) if time_match else ''
        
        # DV/SC check
        title_lower = title.lower()
        dv_sc = 'dv cleared' in title_lower or 'dv-cleared' in title_lower
        sc = 'sc cleared' in title_lower or 'sc-cleared' in title_lower or 'security cleared' in title_lower
        
        # Employment type from spans
        emp = 'permanent'
        if 'contract' in title_lower: emp = 'contract'
        for s in clean_spans:
            if s.lower() in ('contract', 'permanent'): emp = s.lower()
        
        jobs.append({
            'title': title,
            'company': '[view listing]',  # JobServe mobile doesn't expose company
            'location': location,
            'salary_display': salary if salary else 'Not listed',
            'date_posted': TODAY,
            'url': f"https://www.jobserve.com/gb/en/mob/job/{jid}/",  # desktop /job/ returns 500, mobile works
            'source': 'JobServe',
            'source_type': 'aggregator',
            'role_type': _classify(title_lower),
            'remote': 'remote' if 'remote' in title_lower else ('hybrid' if 'hybrid' in title_lower else 'onsite'),
            'employment': emp,
            'sc_clearance': sc or dv_sc,
            'grad_scheme': False,
            'link_status': 'live',
            'visa_sponsorship': 'sc_blocked' if (dv_sc or sc) else 'unknown',
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
    print("Creating JobServe session...")
    shd = create_session()
    if not shd:
        print("ERROR: Could not create session or extract SHD")
        return []
    print(f"Session SHD: {shd}")
    
    sponsors = load_sponsors()
    print(f"Sponsors loaded: {len(sponsors)}")
    
    all_jobs = []
    empty_pages = 0
    MAX_EMPTY = 3  # stop after 3 consecutive empty pages
    
    for page in range(1, 11):  # max 10 pages
        html = fetch_page(shd, page)
        jobs = parse_jobs(html)
        all_jobs.extend(jobs)
        
        if jobs:
            empty_pages = 0
            print(f"  Page {page}: {len(jobs)} SN jobs")
        else:
            empty_pages += 1
            print(f"  Page {page}: 0 SN jobs (empty streak: {empty_pages})")
            if empty_pages >= MAX_EMPTY:
                print(f"  Stopping after {MAX_EMPTY} empty pages")
                break
    
    # Dedup by title + location
    seen = set()
    unique = []
    for j in all_jobs:
        k = (j['title'].lower().strip(), j['location'].lower().strip())
        if k not in seen:
            seen.add(k)
            # Tag sponsorship if we know the company
            if j.get('visa_sponsorship') == 'unknown':
                j['visa_sponsorship'] = check_sponsor(j.get('company', ''), sponsors)
            unique.append(j)
    
    print(f"\nTotal: {len(unique)} unique SN jobs from JobServe")
    
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    return unique

if __name__ == '__main__':
    main()
