#!/usr/bin/env python3
"""
Hunt UK scraper v2.3 — standalone, Playwright-based.

Text layout (single sweep):
  TITLE (SN keyword)
  [location or company first]
  COMPANY NAME  = first substantial non-sentence line after title
  [desc lines]
  LOCATION, UK  = UK_RE match → end of listing
  DATE (M/D/Y)  = date match → end of listing

Output: docs/data/hunt_uk_jobs.json
"""

import json, os, re, sys
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. pip3 install playwright && playwright install chromium")
    sys.exit(1)

URL = 'https://huntukvisasponsors.com/jobs?q=servicenow'
OUT = os.path.expanduser(
    '~/hermes-workspace/servicenow-jobs-digest/docs/data/hunt_uk_jobs.json')
TODAY      = datetime.now().strftime('%Y-%m-%d')
SCRAPED_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

ROLE_KW = re.compile(r'\bservicenow|\bsnow\b', re.IGNORECASE)
UK_RE   = re.compile(
    r'\b(UK|United Kingdom|England|Scotland|Wales|London|Manchester'
    r'|Birmingham|Edinburgh|Glasgow|Bristol|Leeds)\b', re.IGNORECASE)
SC_RE   = re.compile(
    r'security\s+(?:clearance|cleared)|sc\s+clearance|dv\s+clearance'
    r'|developed\s+vetting|bpss',
    re.IGNORECASE)

def _is_noise_line(line):
    """Return True if this line is a candidate-number, site nav, or page boilerplate."""
    l = line.lower().strip()
    # Pure number (candidate index / page number)
    if l.isdigit():
        return True
    # Site nav / boilerplate
    if l in ('home', 'favorites', 'browse jobs', 'save', 'delete', 'report',
             'hunt uk visa sponsors', 'how does it work', 'log in', 'register',
             'you.re seeing delayed', 'days delayed', 'all jobs listed',
             'eligibility', 'check our', 'sign up'):
        return True
    if l.startswith('this job is with'):
        return True
    return False


def _looks_like_company(line):
    """Heuristic: company names start with capital, aren't sentence-start capitalised."""
    if not line or not line[0].isupper():
        return False
    # Don't pick up descriptive lines that happen to start with capital
    starts_sentences = ('the', 'we ', 'our ', 'a ', 'an ', 'this ', 'join ',
                        'about', 'job ', 'due to', 'if ', 'service', 'role')
    low = line.lower()
    if any(low.startswith(w) for w in starts_sentences):
        return False
    return True


def parse_jobs(page_text):
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]
    jobs = []

    for i, line in enumerate(lines):
        if not ROLE_KW.search(line) or len(line) < 12:
            continue

        # Reject page headings / boilerplate that happen to match ROLE_KW
        noise_titles = (
            'days delayed', 'listed below', 'all jobs listed',
            'find jobs from', 'hunt uk visa', 'you.re seeing',
            'browse the extensive',
        )
        if any(n in line.lower() for n in noise_titles):
            continue

        # Reject long sentence-starts (descriptions, not job titles)
        starts_sentences = ('we are', "we're", 'we’re', 'about the',
                            'job summary',
                            'job title', 'this role', 'due to', 'if you',
                            'please', 'join ', 'you will be')
        if any(line.lower().startswith(w) for w in starts_sentences):
            continue

        # Window: title + lines after
        j = i + 1
        company   = None
        block_str = ''

        while j < len(lines) and j < i + 22:
            cur = lines[j]

            # Another title → next listing
            if ROLE_KW.search(cur):
                break

            # UK location → end of listing body
            if UK_RE.search(cur) and len(cur) < 80:
                break

            # US date → end
            if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', cur):
                break

            block_str = (block_str + ' ' + cur) if block_str else cur

            # First non-noise, capitalised non-sentence line = company candidate
            if company is None and not _is_noise_line(cur) and _looks_like_company(cur):
                company = cur

            j += 1

        if not company:
            continue

        listing_block = ' '.join(lines[i: j])

        # UK location
        loc_m = re.search(
            r'(London|Manchester|Birmingham|Edinburgh|Glasgow|Bristol|Leeds'
            r'|England|Scotland|Wales|United Kingdom|Denham|Reading)[\w\s,]*',
            listing_block, re.IGNORECASE)
        location = (loc_m.group(0).strip().rstrip(',')
                    if loc_m else 'United Kingdom')

        # Salary
        sal_m = re.search(
            r'[\£][\d,]+(?:\s*(?:to|-|–)\s*[\£][\d,]+)?(?:\s*(?:GBP|per\s+(?:annum|day|year)))?',
            listing_block)
        salary_display = sal_m.group(0) if sal_m else 'Not listed'

        # SC
        sc = bool(SC_RE.search(listing_block))

        # Employment
        bl = listing_block.lower()
        emp = ('contract' if 'contract' in bl
               else 'temporary' if ('temp' in bl or 'fixed term' in bl)
               else 'permanent')

        # Role type
        tl = line.lower()
        if 'architect' in tl:       rt = 'architect'
        elif 'developer' in tl:     rt = 'developer'
        elif 'consultant' in tl:    rt = 'consultant'
        elif 'director' in tl:      rt = 'manager'
        elif 'manager' in tl:       rt = 'manager'
        elif 'lead' in tl:          rt = 'manager'
        elif 'specialist' in tl:    rt = 'admin'
        elif 'admin' in tl:         rt = 'admin'
        else:                       rt = 'other'

        remote = ('remote' if 'remote' in tl
                  else 'hybrid' if 'hybrid' in tl
                  else 'onsite')

        # Title cleanup: strip inline references like " - 277199"
        clean_title = re.sub(r'\s*-\s*\d{2,}\s*$', '', line).strip()

        jobs.append({
            'title': clean_title,
            'company': company,
            'location': location,
            'salary_display': salary_display,
            'date_posted': TODAY,
            'url': URL,
            'source': 'Hunt UK',
            'source_type': 'aggregator',
            'sn_role': True,
            'role_type': rt,
            'remote': remote,
            'employment': emp,
            'sc_clearance': sc,
            'grad_scheme': False,
            'link_status': 'live',
            'visa_sponsorship': 'unknown',
            'sponsor_licence': False,
            'description': listing_block[:500],
            'scraped_at': SCRAPED_AT,
        })

    return jobs


def scrape():
    print(f'Fetching Hunt UK: {URL}')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
                                    args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = browser.new_page(viewport={'width': 1280, 'height': 900})
        page.goto(URL, wait_until='domcontentloaded', timeout=35000)
        page.wait_for_timeout(5000)
        raw = page.inner_text('body')
        browser.close()

    jobs = parse_jobs(raw)
    print(f'  Parsed {len(jobs)} Hunt UK SN jobs')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print(f'\n  {len(jobs)} jobs -> {OUT}')
    for j in jobs:
        sc_b = "🔒" if j.get('sc_clearance') else "  "
        print(f'  {sc_b} {j["title"][:62]} |'
              f' {j["company"][:28]} | {j["location"]}')
    return jobs


if __name__ == '__main__':
    scrape()
