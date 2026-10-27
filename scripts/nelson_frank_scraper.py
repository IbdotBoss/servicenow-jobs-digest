#!/usr/bin/env python3
"""
Nelson Frank scraper v2.2 — standalone, Playwright-based.
Fetches category sub-pages (JS-rendered, Playwright required).

Job layouts observed:
  Digit-prefixed:    "1\\nTITLE\\nLOCATION\\nSALARY\\n..."  (architect page style)
  Direct title:      "TITLE\\nLOCATION\\nSALARY\\n..."       (consultant/other page style)
  Separator:         "Save\\nApply" (between jobs) or "Save\\nApply\\n\\nnew"

Categories (per references/nelson-frank-scraping.md):
  /servicenow-consultant-jobs
  /servicenow-other-jobs
  /servicenow-architect-jobs
"""

import json, os, re, sys
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. pip3 install playwright && playwright install chromium")
    sys.exit(1)

def _chrome_bin():
    """Auto-discover a usable Chromium binary in the Playwright cache.
    Returns None on platforms where Playwright manages its own browser (e.g. Windows),
    so launch() falls back to default behaviour. On headless Linux VPS where the
    pinned browser can't be downloaded, this picks up an already-cached build."""
    import glob as _g
    cands = sorted(_g.glob(os.path.expanduser('~/.cache/ms-playwright/chromium-*/chrome-linux/chrome')))
    return cands[-1] if cands else None

CATEGORY_URLS = [
    ('https://www.nelsonfrank.com/jobs/?show_results=1&query=servicenow&location=London', 'london'),
]

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'nelson_frank_jobs.json'
)
TODAY = datetime.now().strftime('%Y-%m-%d')
SCRAPED_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

UK_RE   = re.compile(r'\b(UK|United Kingdom|England|Scotland|Wales|London|Manchester'
                     r'|Birmingham|Edinburgh|Glasgow|Bristol|Leeds|Reading)\b', re.IGNORECASE)
SN_RE   = re.compile(
    r'\b(servicenow|snow platform|it service management|itsm|itom|hrsd|csm|csam|secops)\b',
    re.IGNORECASE)
NOISE_RE = re.compile(r'\b(sales|recruiter|account manager|business development|bdm)\b')
SC_RE   = re.compile(r'(?:security\s+(?:clearance|cleared)|sc\s+clearance?|dv\s+clearance?|developed\s+vetting|bpss|eligib(?:le|ility)\s+for\s+sc)', re.IGNORECASE)

ROLE_KEYWORDS = {
    'architect': 'architect',
    'developer': 'developer',
    'engineer':  'developer',
    'consultant':'consultant',
    'manager':   'manager',
    'lead':      'manager',
    'analyst':   'analyst',
    'admin':     'admin',
    'specialist':'other',
    'technician':'other',
}

def classify(title):
    tl = title.lower()
    for kw, cls in ROLE_KEYWORDS.items():
        if kw in tl:
            return cls
    return 'other'

def classify_remote(title):
    tl = title.lower()
    if 'remote' in tl:   return 'remote'
    if 'hybrid' in tl:   return 'hybrid'
    return 'onsite'

def classify_emp(title):
    tl = title.lower()
    return 'contract' if 'contract' in tl else 'permanent'

def parse_jobs_from_page(page_text):
    """Parse job listings from fully rendered page text.

    RECORD FORMAT (changed ~Aug 2026 — the old 'Save/Apply' card layout is gone):
        Ref. No. a0MP900000AKMWTMA5
        <blank>
        TITLE
        Published
        October 10, 2026
        Location
        Chicago, Illinois, United States of America
        Brand
        Nelson Frank
        Job Type
        Contract
        Salary/Rate
        USD 60.00 to 100.00
        Products
        Netsuite
        Job Description
        ...

    The category sub-pages (/servicenow-consultant-jobs etc.) now return an
    UNFILTERED global listing (identical results across all three, most of them
    US/France/Singapore) and /servicenow-other-jobs is a 404. So we target the
    /jobs/ search endpoint with query=servicenow + location=London, which is
    UK-relevant, then filter on the Location field.
    """
    jobs = []

    # Split into records on the 'Ref. No.' marker.
    recs = re.split(r'Ref\. No\.\s*\S+', page_text)
    for body in recs:
        if not body.strip():
            continue
        m = re.search(
            r'\n\s*\n?\s*(?P<title>.+?)\s*\nPublished\s*\n\s*(?P<pub>.+?)'
            r'\nLocation\s*\n\s*(?P<loc>.+?)'
            r'\nBrand\s*\n\s*(?P<brand>.+?)\s*\n',
            body, re.DOTALL)
        if not m:
            continue
        title = m.group('title').strip()
        location = m.group('loc').strip()
        brand = m.group('brand').strip()
        published = m.group('pub').strip()

        if not SN_RE.search(title) and not SN_RE.search(body[:600]):
            continue
        if NOISE_RE.search(title):
            continue
        if not UK_RE.search(location):
            continue

        # Normalise 'October 10, 2026' -> '2026-10-10'
        date_posted = TODAY
        for fmt in ('%B %d, %Y', '%b %d, %Y'):
            try:
                date_posted = datetime.strptime(published, fmt).strftime('%Y-%m-%d')
                break
            except ValueError:
                continue

        # Salary
        sal = re.search(r'Salary/Rate\s*\n\s*(.+?)\s*\n', body)
        salary = sal.group(1).strip() if sal else 'Not listed'

        # Job Type
        jt = re.search(r'Job Type\s*\n\s*(.+?)\s*\n', body)
        employment = (jt.group(1).strip().lower() if jt else 'permanent')
        if employment not in ('contract', 'temporary', 'permanent'):
            employment = 'permanent'

        desc_m = re.search(r'Job Description\s*\n\s*\n?(.+)', body, re.DOTALL)
        desc = re.sub(r'\s+', ' ', desc_m.group(1))[:500] if desc_m else ''

        sc = bool(SC_RE.search(title + ' ' + desc))

        # Employer is the Brand (agency subsidiary) — keep it, it's the real
        # posting entity; Nelson Frank / Anderson Frank / Nigel Frank.
        jobs.append({
            'title': title,
            'company': brand or 'Nelson Frank (agency)',
            'location': location,
            'salary_display': salary,
            'date_posted': date_posted,
            'url': 'https://www.nelsonfrank.com/jobs/?show_results=1&query=servicenow&location=London',
            'source': 'Nelson Frank',
            'source_type': 'agency',
            'sn_role': True,
            'role_type': classify(title),
            'remote': classify_remote(title + ' ' + desc),
            'employment': employment,
            'sc_clearance': sc,
            'grad_scheme': False,
            'link_status': 'live',
            'visa_sponsorship': 'agency_unknown',
            'sponsor_licence': False,
            'description': desc,
            'scraped_at': SCRAPED_AT,
        })

    return jobs


def scrape():
    print(f'Fetching Nelson Frank via Playwright ({len(CATEGORY_URLS)} pages)...')
    all_jobs = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=_chrome_bin(), args=['--no-sandbox','--disable-setuid-sandbox'])

        for url, category in CATEGORY_URLS:
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            try:
                print(f'\n→ {category}: {url}')
                page.goto(url, wait_until='domcontentloaded', timeout=35000)
                page.wait_for_timeout(5000)

                raw = page.inner_text('body')
                jobs = parse_jobs_from_page(raw)

                for j in jobs:
                    key = (j['title'].lower(), j.get('location','').lower())
                    if key not in seen:
                        seen.add(key)
                        all_jobs.append(j)

                print(f'  {len(jobs)} new UK SN jobs (total unique: {len(all_jobs)})')
            except Exception as e:
                print(f'  ERROR: {e}')
            finally:
                page.close()

        browser.close()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)

    print(f'\n✅ {len(all_jobs)} UK SN Nelson Frank jobs → {OUT}')
    for j in all_jobs:
        sc_b = '🔒' if j.get('sc_clearance') else '  '
        print(f'  {sc_b} {j["title"][:72]} | {j["location"]} | {"SC" if j.get("sc_clearance") else ""}')
    return all_jobs


if __name__ == '__main__':
    scrape()
