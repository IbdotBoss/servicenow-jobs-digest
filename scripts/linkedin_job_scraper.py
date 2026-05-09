#!/usr/bin/env python3
"""
LinkedIn job scraper v3.5 — curl+Voyager, stealthy.
Same approach that worked (found 59 jobs) but SLOW: 10 pages max, 3-5s delays.
The old account got blocked because we did 40 pages in 2 minutes.
New account + slow scraping = no block.

Usage:
  python3 scripts/linkedin_job_scraper.py              # daily delta (5 pages)
  python3 scripts/linkedin_job_scraper.py --full        # catch-up (15 pages)
"""
import subprocess, re, json, html as htmlmod, csv, sys, os, time, random
from datetime import datetime

COOKIE_FILE = '/tmp/li_cookies.txt'
SPONSOR_CSV = os.path.expanduser('~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv')
OUTPUT_DIR = os.path.expanduser('~/hermes-workspace/servicenow-jobs-digest/docs/data')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'linkedin_jobs.json')

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
SN_KEYWORDS = ['servicenow', 'snow ', 'itsm', 'csdm', 'csam', 'grcc', 'irr', 'secops', 'itom', 'hrsd', 'fsm', 'csm ']
NOISE_KEYWORDS = ['service desk', 'it support', 'helpdesk', 'desktop support', 'technical support', 'tech bar', 'mac engineer', 'payroll', 'endpoint security', 'salesforce']

SC_COMPANIES = {'bae systems', 'qinetiq', 'leonardo', 'thales', 'mbda', 'rolls-royce',
                'gchq', 'atkinsréalis', 'atkins realis', 'atkins', 'accenture'}
AGENCY_COMPANIES = {'huxley', 'nelson frank', 'linking humans', 'harnham', 'deerfoot',
                    'experis', 'hays', 'akkodis', 'marshall wolfe', 'global technology solutions',
                    'la fosse', 'sanderson', 'robert half', 'michael page', 'computer futures',
                    'harvey nash', 'sthree', 'eteam', 'ubique systems', 'gios technology'}

def harvest_cookies():
    try:
        import browser_cookie3
        cj = browser_cookie3.brave(domain_name='linkedin.com')
        li_at = [c for c in cj if c.name == 'li_at']
        if not li_at:
            cj_all = browser_cookie3.brave()
            li_at = [c for c in cj_all if c.name == 'li_at' and 'linkedin' in c.domain]
        if li_at:
            with open(COOKIE_FILE, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                for c in cj:
                    if 'linkedin' in c.domain:
                        d = c.domain if c.domain.startswith('.') else '.' + c.domain
                        s = 'TRUE' if c.secure else 'FALSE'
                        e = str(int(c.expires)) if c.expires else '0'
                        f.write(f"{d}\tTRUE\t{c.path}\t{s}\t{e}\t{c.name}\t{c.value}\n")
            print(f"✅ {len(li_at)} li_at cookies from Brave")
            return True
        print("⚠️ No li_at in Brave cookies")
        return False
    except Exception as e:
        print(f"⚠️ Cookie harvest error: {e}")
        return False

def verify_auth():
    r = subprocess.run(['curl', '-s', '-b', COOKIE_FILE, '-A', UA,
        '-o', '/dev/null', '-w', '%{http_code}',
        'https://www.linkedin.com/jobs/search/?keywords=test&start=0&count=1'],
        capture_output=True, text=True, timeout=10)
    return r.stdout.strip() == '200'

def load_sponsors():
    sponsors = {}
    with open(SPONSOR_CSV, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            org = row.get('Organisation Name', '').strip().lower()
            route = row.get('Route', '').lower()
            rating = row.get('Type & Rating', '').lower()
            if org and 'skilled worker' in route and 'a rating' in rating:
                sponsors[org] = True
    return sponsors

def check_sponsor(company, sponsors):
    if not company: return 'unknown'
    name = company.lower().strip().split(' - ')[0].split(' (')[0]
    for a in AGENCY_COMPANIES:
        if a in name: return 'agency_unknown'
    for s in sponsors:
        if name in s or s in name:
            for sc in SC_COMPANIES:
                if sc in name or sc in s: return 'sc_blocked'
            return 'verified'
    return 'unknown'

def extract_jobs(html_text):
    blocks = re.findall(r'<code[^>]*>(.*?)</code>', html_text, re.DOTALL)
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
                tl = title.lower()
                if any(k in tl for k in NOISE_KEYWORDS): continue
                if not any(k in tl for k in SN_KEYWORDS): continue
                company = c.get('primaryDescription', {}).get('text', 'N/A')
                sec = c.get('secondaryDescription', {})
                location = sec.get('text', 'N/A') if isinstance(sec, dict) else 'N/A'
                urn = c.get('preDashNormalizedJobPostingUrn', '')
                jid = urn.split(':')[-1] if urn else 'N/A'
                jobs.append({
                    'title': title, 'company': company, 'location': location,
                    'url': f'https://www.linkedin.com/jobs/view/{jid}' if jid != 'N/A' else '',
                    'source': 'LinkedIn'
                })
        except: continue
    return jobs

def scrape(full=False):
    # Harvest cookies
    print("Harvesting LinkedIn cookies from Brave...")
    if not harvest_cookies():
        print("❌ No cookies — skip LinkedIn")
        return []
    if not verify_auth():
        print("❌ Cookies invalid — skip LinkedIn")
        return []

    sponsors = load_sponsors()
    max_pages = 15 if full else 5
    time_filter = '' if full else '&f_TPR=r86400'
    filter_label = 'ALL TIME' if full else 'last 24h'
    print(f"✅ Auth OK — scraping ({filter_label}, {max_pages} pages, slow mode 3-5s)")

    all_jobs = []
    for page in range(max_pages):
        start = page * 25
        url = (f'https://www.linkedin.com/jobs/search/'
               f'?keywords=ServiceNow&location=United%20Kingdom'
               f'&geoId=101165590{time_filter}&start={start}&count=25')
        try:
            result = subprocess.run(['curl', '-s', '-b', COOKIE_FILE, '-A', UA,
                '-H', 'Accept: text/html,application/xhtml+xml',
                '-H', 'Accept-Language: en-US,en;q=0.9', url],
                capture_output=True, text=True, timeout=30)
            page_jobs = extract_jobs(result.stdout)
            if page_jobs:
                print(f"  Page {page}: {len(page_jobs)} SN jobs")
                all_jobs.extend(page_jobs)
            else:
                print(f"  Page {page}: 0 jobs → end")
                if page > 2: break
            # 🐌 CRITICAL: slow down to avoid bot detection
            time.sleep(random.uniform(3, 5))
        except subprocess.TimeoutExpired:
            print(f"  Page {page}: timeout")
            continue
        except Exception as e:
            print(f"  Page {page}: {e}")
            continue

    # Dedupe
    seen, unique = set(), []
    for j in all_jobs:
        key = (j['title'].lower().strip(), j['company'].split(' - ')[0].strip().lower())
        if key not in seen:
            seen.add(key)
            j['visa_sponsorship'] = check_sponsor(j['company'], sponsors)
            unique.append(j)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(unique, f, indent=2)

    verified = sum(1 for r in unique if r.get('visa_sponsorship') == 'verified')
    print(f"\n✅ {len(unique)} SN LinkedIn jobs ({filter_label}, {verified} sponsors)")
    print(f"   Saved to {OUTPUT_FILE}")
    for r in unique[:5]:
        t = {'verified': '🟢', 'sc_blocked': '🔒', 'agency_unknown': '🏢', 'unknown': '❓'}
        print(f"   {t.get(r.get('visa_sponsorship','?'), '?')} {r['title'][:55]} | {r['company']}")
    return unique

if __name__ == '__main__':
    full = '--full' in sys.argv
    scrape(full=full)
