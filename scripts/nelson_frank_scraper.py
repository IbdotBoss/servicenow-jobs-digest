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

CATEGORY_URLS = [
    ('https://www.nelsonfrank.com/servicenow-consultant-jobs', 'consultant'),
    ('https://www.nelsonfrank.com/servicenow-other-jobs',       'other'),
    ('https://www.nelsonfrank.com/servicenow-architect-jobs',   'architect'),
]

OUT = os.path.expanduser(
    '~/hermes-workspace/servicenow-jobs-digest/docs/data/nelson_frank_jobs.json'
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
    """Parse job listings from fully rendered page text."""
    jobs = []

    # Split into blocks: "Save\nApply" or "Save\nApply\n\nnew" are the delimiters
    sep_re = re.compile(r'\nSave\s*\nApply(?:\s*\nnew)?')
    blocks = sep_re.split(page_text)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) < 4:
            continue

        # ── Locate title ──
        # Title is either:
        #  a) lines[i+1] where lines[i] is a pure digit (job number), OR
        #  b) lines[0] if lines[0] is a substantive title line (noise check below)
        start_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^\d+$', line):
                # Lines before the number? Unlikely, but skip them
                title_idx = i + 1
                if title_idx < len(lines):
                    start_idx = title_idx
                break

        if start_idx is None:
            # No digit prefix — title is the first non-trivial line
            start_idx = 0

        title = lines[start_idx]

        # Noise filters
        # Drop page headings like "ServiceNow Consultant Jobs", "ServiceNow Architect Jobs"
        if ' Jobs' in title or ' Jobs ' in title:
            continue
        if not SN_RE.search(title):
            continue
        if NOISE_RE.search(title):
            continue

        # ── Location ──
        # Line after title is usually the location (but title itself might be
        # a "add new" marker — check for "new" or "Browse the extensive range")
        loc_idx = start_idx + 1
        if lines[loc_idx].lower() in ('new', 'recently added', 'browse the extensive range'):
            loc_idx += 1
        location_line = lines[loc_idx] if loc_idx < len(lines) else ''

        # Check UK across title + location_line + first 3 lines of desc
        desc_lines = lines[loc_idx + 2: loc_idx + 10]  # skip LOCATION and SALARY
        context = ' '.join(lines[start_idx: start_idx + 4] + desc_lines)
        if not UK_RE.search(context) and not UK_RE.search(location_line):
            continue

        # ── Salary ──
        salary_cand_idx = loc_idx + 1
        salary = lines[salary_cand_idx] if salary_cand_idx < len(lines) else 'Not listed'
        if not re.search(r'[\$\£]|GBP|USD|per\s+annum', salary, re.IGNORECASE):
            salary = 'Not listed'

        # ── Description ──
        desc_idx = next((i for i, l in enumerate(lines) if 'job description' in l.lower()), -1)
        desc = ' '.join(lines[desc_idx + 1: desc_idx + 8])[:500] if desc_idx >= 0 else ''

        # ── SC check ──
        sc_text = context + ' ' + desc
        sc = bool(SC_RE.search(sc_text))

        jobs.append({
            'title': title,
            'company': 'Nelson Frank (agency)',
            'location': location_line if UK_RE.search(location_line) else 'United Kingdom',
            'salary_display': salary,
            'date_posted': TODAY,
            'url': 'https://www.nelsonfrank.com/servicenow-jobs-in-united-kingdom',
            'source': 'Nelson Frank',
            'source_type': 'agency',
            'sn_role': True,
            'role_type': classify(title),
            'remote': classify_remote(title),
            'employment': classify_emp(title),
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
        browser = p.chromium.launch(headless=True, args=['--no-sandbox','--disable-setuid-sandbox'])

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
