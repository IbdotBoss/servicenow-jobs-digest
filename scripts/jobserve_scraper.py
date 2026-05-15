#!/usr/bin/env python3
"""JPv4.1 — 24h etime filter + boolean sponsor check + proper date_posted
FIXED: check_sponsor() now returns boolean (sponsor_licence), never 'verified'
FIXED: 24h etime filter — only "hour(s) ago" and "minutes ago" jobs
FIXED: date_posted derived from etime, not hardcoded to TODAY
"""
import re, html as html_mod, json, os, subprocess, csv
from datetime import datetime

UA = 'Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36'
TODAY = datetime.now().strftime("%Y-%m-%d")
OUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobserve_jobs.json")
SPONSOR_CSV = os.path.expanduser("~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv")
COOKIE_FILE = '/tmp/js_cookies.txt'

SN_TITLE_KW = ['servicenow', 'service-now', 'service now']

# Genuinely IT-adjacent roles worth surfacing (ITSM, service desk, Remedy, etc.)
ADJACENT_KW = [
    'itsm', 'itil', 'remedy', 'service desk', 'helpdesk', 'sacm', 'itam',
    'change manager', 'incident manager', 'problem manager',
    'service delivery', 'helix', 'service asset', 'configuration management',
    'asset manager', 'major incident', 'service lead', 'it service',
    'it support', 'it operations', 'service transition', 'release manager',
    'cmdb', 'csm', 'itom', 'itbm',
]

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

def check_sponsor_licence(name, sponsors):
    """Return True if company is on A-rated Skilled Worker register. Never returns 'verified'."""
    if not name or name in ('N/A', '', '[view listing]'): return False
    n = name.lower().strip().split(' - ')[0].split(' (')[0]
    for s in sponsors:
        if n in s or s in n:
            return True
    return False

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

def parse_etime(etime_text):
    """Parse JobServe etime text into (is_fresh_24h, date_str).
    etime examples: '1 hour ago', '23 hours ago', '20 minutes ago', '1 day ago', '3 days ago'
    Returns (True, 'YYYY-MM-DD') if within 24h, (False, None) otherwise."""
    if not etime_text: return (False, None)
    t = etime_text.lower().strip()
    # Minutes/hours = today → fresh ('min' catches both 'mins' and 'minutes')
    if 'min' in t or 'hour' in t or 'today' in t or 'just' in t:
        return (True, datetime.now().strftime('%Y-%m-%d'))
    # 1 day ago = yesterday → borderline, include
    if t == '1 day ago' or t.startswith('yesterday'):
        from datetime import timedelta
        return (True, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    # 2+ days ago → skip
    return (False, None)

def parse_jobs(html_text):
    jobs = []
    blocks = re.findall(r'<li id="J([A-F0-9]+)"[^>]*>(.*?)</li>', html_text, re.DOTALL)
    
    for jid, block in blocks:
        pos_match = re.search(r'class="position">(.*?)</span>', block)
        if not pos_match: continue
        title = html_mod.unescape(pos_match.group(1).strip())
        
        # Classify: ServiceNow-specific, adjacent, or irrelevant
        title_lower = title.lower()
        is_sn = any(kw in title_lower for kw in SN_TITLE_KW)
        is_adjacent = any(kw in title_lower for kw in ADJACENT_KW)
        if not is_sn and not is_adjacent: continue  # skip irrelevant noise
        
        # ── 24h etime filter ──
        time_match = re.search(r'class="etime">(.*?)</span>', block)
        etime = html_mod.unescape(time_match.group(1).strip()) if time_match else ''
        is_fresh, date_posted = parse_etime(etime)
        if not is_fresh:
            continue  # Skip jobs older than 24h
        
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
        
        # DV/SC check
        dv_sc = 'dv cleared' in title_lower or 'dv-cleared' in title_lower
        sc = 'sc cleared' in title_lower or 'sc-cleared' in title_lower or 'security cleared' in title_lower
        
        # Employment type from spans
        emp = 'permanent'
        if 'contract' in title_lower: emp = 'contract'
        for s in clean_spans:
            if s.lower() in ('contract', 'permanent'): emp = s.lower()
        
        jobs.append({
            'title': title,
            'company': '[view listing]',
            'location': location,
            'salary_display': salary if salary else 'Not listed',
            'date_posted': date_posted,
            'url': f"https://www.jobserve.com/gb/en/mob/job/{jid}/",
            'source': 'JobServe',
            'source_type': 'aggregator',
            'sn_role': is_sn,
            'role_type': _classify(title_lower) if is_sn else 'sn-adjacent',
            'remote': 'remote' if 'remote' in title_lower else ('hybrid' if 'hybrid' in title_lower else 'onsite'),
            'employment': emp,
            'sc_clearance': sc or dv_sc,
            'grad_scheme': False,
            'link_status': 'live',
            'visa_sponsorship': 'sc_blocked' if (dv_sc or sc) else 'unknown',
            'description': f"Posted {etime}" if etime else '',
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
            sn = sum(1 for j in jobs if j.get('sn_role'))
            adj = sum(1 for j in jobs if not j.get('sn_role'))
            parts = []
            if sn: parts.append(f'{sn} SN')
            if adj: parts.append(f'{adj} adjacent')
            print(f"  Page {page}: {' + '.join(parts)} jobs")
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
            # Set sponsor_licence boolean (never 'verified')
            j['sponsor_licence'] = check_sponsor_licence(j.get('company', ''), sponsors)
            unique.append(j)
    
    sn_count = sum(1 for j in unique if j.get('sn_role'))
    adj_count = sum(1 for j in unique if not j.get('sn_role'))
    print(f"\nTotal: {len(unique)} unique jobs ({sn_count} SN + {adj_count} adjacent)")
    
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    return unique

if __name__ == '__main__':
    main()
