#!/usr/bin/env python3
"""
LinkedIn Voyager API job scraper — v2.0.
Auto-harvests cookies from Brave each run. Uses --full for catch-up (no time filter).

Usage: python3 scripts/linkedin_scraper.py [--max-pages 40] [--full]
"""
import subprocess, re, json, html as htmlmod, csv, sys, os, argparse
from pathlib import Path

# ── Config ──────────────────────────────────────────────────
SN_KEYWORDS = ['servicenow', 'snow ', 'itsm', 'csdm', 'csam', 'grcc', 'irr', 'secops', 'itom', 'hrsd', 'fsm', 'csm ']
NOISE_KEYWORDS = ['service desk', 'it support', 'helpdesk', 'desktop support', 'technical support', 'tech bar', 'mac engineer', 'payroll', 'endpoint security', 'salesforce']
COOKIE_FILE = '/tmp/li_cookies.txt'
SPONSOR_CSV = os.path.expanduser('~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv')
OUTPUT_FILE = os.path.expanduser('~/hermes-workspace/servicenow-jobs-digest/docs/data/linkedin_jobs.json')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

SC_COMPANIES = {'bae systems', 'qinetiq', 'leonardo', 'thales', 'mbda', 'rolls-royce', 
                'gchq', 'atkinsréalis', 'atkins realis', 'atkins'}

def harvest_cookies():
    """Harvest LinkedIn cookies from running Brave browser. Returns True if li_at found."""
    try:
        import browser_cookie3
        cj = browser_cookie3.brave(domain_name='linkedin.com')
        li_at = [c for c in cj if c.name == 'li_at']
        if not li_at:
            # Try without domain filter
            cj_all = browser_cookie3.brave()
            li_at = [c for c in cj_all if c.name == 'li_at' and 'linkedin' in c.domain]
        
        if li_at:
            # Save in Netscape format
            with open(COOKIE_FILE, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                for c in cj:
                    if 'linkedin' in c.domain:
                        domain = c.domain if c.domain.startswith('.') else '.' + c.domain
                        flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                        secure = 'TRUE' if c.secure else 'FALSE'
                        expiry = str(int(c.expires)) if c.expires else '0'
                        f.write(f"{domain}\t{flag}\t{c.path}\t{secure}\t{expiry}\t{c.name}\t{c.value}\n")
            print(f"✓ Harvested {len(cj)} LinkedIn cookies (li_at found)")
            return True
        else:
            print("⚠ No li_at cookie found — LinkedIn session may be expired")
            # Save what we have anyway
            with open(COOKIE_FILE, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                for c in cj_all:
                    if 'linkedin' in c.domain:
                        domain = c.domain if c.domain.startswith('.') else '.' + c.domain
                        flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                        secure = 'TRUE' if c.secure else 'FALSE'
                        expiry = str(int(c.expires)) if c.expires else '0'
                        f.write(f"{domain}\t{flag}\t{c.path}\t{secure}\t{expiry}\t{c.name}\t{c.value}\n")
            return False
    except Exception as e:
        print(f"⚠ Cookie harvest failed: {e}")
        return False

def verify_auth():
    """Quick check if cookies are still valid."""
    result = subprocess.run(['curl', '-s', '-b', COOKIE_FILE, '-A', UA,
        '-o', '/dev/null', '-w', '%{http_code}',
        'https://www.linkedin.com/jobs/search/?keywords=test&start=0&count=1'],
        capture_output=True, text=True, timeout=10)
    return result.stdout.strip() == '200'

def load_sponsors():
    sponsors = set()
    try:
        with open(SPONSOR_CSV, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                route = row.get('Route', '')
                rating = row.get('Type & Rating', '')
                if 'skilled worker' in route.lower() and 'a rating' in rating.lower():
                    sponsors.add(row.get('Organisation Name', '').strip().lower())
    except: pass
    return sponsors

def check_sponsor(company_name, sponsors):
    name_lower = company_name.lower().strip().split(' - ')[0].split(' (')[0]
    for s in sponsors:
        if name_lower in s or s in name_lower:
            for sc in SC_COMPANIES:
                if sc in name_lower or sc in s:
                    return 'sc_blocked'
            return 'verified'
    return 'unknown'

def extract_jobs_from_page(html):
    blocks = re.findall(r'<code[^>]*>(.*?)</code>', html, re.DOTALL)
    jobs = []
    for raw in blocks:
        try:
            data = json.loads(htmlmod.unescape(raw))
            cards = [x for x in data.get('included', [])
                    if x.get('$type') == 'com.linkedin.voyager.dash.jobs.JobPostingCard']
            if not cards or len(cards) < 3: continue
            for c in cards:
                title = c.get('jobPostingTitle', c.get('title', {}).get('text', '')).strip()
                if not title: continue
                title_lower = title.lower()
                if any(kw in title_lower for kw in NOISE_KEYWORDS): continue
                if not any(kw in title_lower for kw in SN_KEYWORDS): continue
                
                company = c.get('primaryDescription', {}).get('text', 'N/A')
                secondary = c.get('secondaryDescription', {})
                location = secondary.get('text', 'N/A') if isinstance(secondary, dict) else 'N/A'
                norm_urn = c.get('preDashNormalizedJobPostingUrn', '')
                jid = norm_urn.split(':')[-1] if norm_urn else 'N/A'
                footer = c.get('footerText', {}).get('text', '') if isinstance(c.get('footerText'), dict) else ''
                
                jobs.append({
                    'linkedin_id': jid, 'title': title, 'company': company,
                    'location': location, 'url': f'https://www.linkedin.com/jobs/view/{jid}' if jid != 'N/A' else '',
                    'footer': footer, 'source': 'linkedin'
                })
        except: continue
    return jobs

def scrape(max_pages=40, full=False):
    # Step 1: Harvest cookies from Brave
    print("Harvesting LinkedIn cookies from Brave...")
    has_auth = harvest_cookies()
    if not has_auth:
        print("❌ No li_at cookie — LinkedIn auth required. Skipping LinkedIn scrape.")
        return []
    
    # Step 2: Verify auth
    if not verify_auth():
        print("❌ Cookies invalid (not 200). LinkedIn session expired.")
        return []
    print("✓ Auth verified")
    
    sponsors = load_sponsors()
    print(f"Loaded {len(sponsors)} sponsors")
    
    # Step 3: Scrape
    time_filter = '' if full else '&f_TPR=r86400'  # --full = no filter, default = 24h
    filter_label = 'ALL TIME' if full else 'last 24h'
    print(f"Scraping LinkedIn ({filter_label}, max {max_pages} pages)...")
    
    all_jobs = []
    for page in range(max_pages):
        start = page * 25
        url = (f'https://www.linkedin.com/jobs/search/'
               f'?keywords=ServiceNow&location=United%20Kingdom'
               f'&geoId=101165590{time_filter}'
               f'&start={start}&count=25')
        try:
            result = subprocess.run([
                'curl', '-s', '-b', COOKIE_FILE, '-A', UA,
                '-H', 'Accept: text/html,application/xhtml+xml',
                '-H', 'Accept-Language: en-US,en;q=0.9', url
            ], capture_output=True, text=True, timeout=30)
            
            page_jobs = extract_jobs_from_page(result.stdout)
            if not page_jobs and page > 3:
                print(f"  Page {page}: empty → end")
                break
            if page_jobs:
                print(f"  Page {page}: {len(page_jobs)} SN jobs (first: {page_jobs[0]['title'][:50]})")
            all_jobs.extend(page_jobs)
        except subprocess.TimeoutExpired:
            print(f"  Page {page}: timeout")
            continue
        except Exception as e:
            print(f"  Page {page}: error — {e}")
            continue
    
    # Dedupe by title + normalized company
    seen = set()
    unique = []
    for j in all_jobs:
        company_key = j['company'].split(' - ')[0].split(' (')[0].strip().lower()
        key = (j['title'].lower().strip(), company_key)
        if key not in seen:
            seen.add(key)
            j['sponsor_verified'] = check_sponsor(j['company'], sponsors)
            unique.append(j)
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(unique, f, indent=2)
    
    verified = sum(1 for j in unique if j['sponsor_verified'] == 'verified')
    print(f"\n✓ {len(unique)} unique SN LinkedIn jobs ({filter_label})")
    print(f"  {verified} from verified sponsors")
    print(f"  Saved to {OUTPUT_FILE}")
    return unique

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-pages', type=int, default=40)
    parser.add_argument('--full', action='store_true', help='Scrape ALL active jobs (no 24h time filter)')
    args = parser.parse_args()
    scrape(max_pages=args.max_pages, full=args.full)
