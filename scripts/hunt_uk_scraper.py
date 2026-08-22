#!/usr/bin/env python3
"""
Hunt UK scraper v2.4 — Playwright href extraction.

FIX (v2.4): The previous inner_text-based parser lost the job URL (hrefs are
stripped by inner_text), so every job fell back to the search-page URL
(huntukvisasponsors.com/jobs?q=servicenow). That URL is in rebuild_master's
BAD_URL_PATTERNS, so ALL Hunt UK jobs were auto-expired and contributed ZERO
active listings.

This version queries the real <a href="/job/SLUG"> anchors and parses the
card text for title/company/location. /job/ URLs pass the bad-URL filter, so
Hunt UK jobs now contribute real, linkable, active listings.

Output: docs/data/hunt_uk_jobs.json
"""

import json, os, re, glob as _g, sys
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

ROLE_KW = re.compile(r'servicenow|\bsnow\b', re.IGNORECASE)
UK_RE   = re.compile(
    r'\b(UK|United Kingdom|England|Scotland|Wales|London|Manchester'
    r'|Birmingham|Edinburgh|Glasgow|Bristol|Leeds|Reading|Sutton|Dartford'
    r'|Prestwick|Colney|Anywhere)\b', re.IGNORECASE)
SC_RE   = re.compile(
    r'security\s+(?:clearance|cleared)|sc\s+clearance|dv\s+clearance'
    r'|developed\s+vetting|bpss', re.IGNORECASE)
# Sponsorship-likelihood tokens that appear inside the card text
TOKENS = {'high', 'medium', 'low', 'ineligible'}


def _chrome_bin():
    """Auto-discover a cached Chromium binary on headless Linux VPS."""
    import glob as _g
    cands = sorted(_g.glob(os.path.expanduser('~/.cache/ms-playwright/chromium-*/chrome-linux/chrome')))
    return cands[-1] if cands else None


def classify(title):
    t = title.lower()
    if 'architect' in t:       return 'architect'
    if 'developer' in t:       return 'developer'
    if 'consultant' in t:      return 'consultant'
    if 'presales' in t or 'pre-sales' in t: return 'consultant'
    if 'manager' in t or 'lead' in t or 'director' in t: return 'manager'
    if 'admin' in t:           return 'admin'
    if 'specialist' in t:      return 'other'
    if 'analyst' in t:         return 'analyst'
    return 'other'


def classify_remote(title):
    t = title.lower()
    if 'remote' in t:   return 'remote'
    if 'hybrid' in t:   return 'hybrid'
    return 'onsite'


def classify_emp(title):
    t = title.lower()
    if 'contract' in t: return 'contract'
    if 'temp' in t or 'fixed term' in t: return 'temporary'
    return 'permanent'


def parse_card(href, txt):
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    lines = [l for l in lines if l.lower() not in TOKENS]
    if not lines:
        return None
    title = lines[0]
    if not ROLE_KW.search(title):
        return None

    # Company is the line immediately after the title (stable card layout)
    company = lines[1] if len(lines) > 1 else 'Unknown'

    # Location: a later line that looks like a place but is NOT the company
    # name and not a pure company-style name (LIMITED/LTD).
    location = 'United Kingdom'
    for l in lines[2:]:
        if UK_RE.search(l) and 'LIMITED' not in l.upper() and 'LTD' not in l.upper():
            location = l.rstrip('—').strip() or 'United Kingdom'
            break

    # Posted date (informational; card shows relative age)
    posted = ''
    for l in lines[1:]:
        low = l.lower()
        if re.search(r'\d+\s*(?:d|day|h|hour|w|week|mo|month)\s*ago', low) or low in ('just now', 'today'):
            posted = l
            break

    block = ' '.join(lines)
    sc = bool(SC_RE.search(block))

    return {
        'title': title,
        'company': company,
        'location': location,
        'salary_display': 'Not listed',
        'date_posted': TODAY,
        'url': href,
        'source': 'Hunt UK',
        'source_type': 'aggregator',
        'sn_role': True,
        'role_type': classify(title),
        'remote': classify_remote(title),
        'employment': classify_emp(title),
        'sc_clearance': sc,
        'grad_scheme': False,
        'link_status': 'live',
        'visa_sponsorship': 'unknown',
        'sponsor_licence': False,
        'description': block[:500],
        'scraped_at': SCRAPED_AT,
    }


def scrape():
    print(f'Fetching Hunt UK: {URL}')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
                                    executable_path=_chrome_bin(),
                                    args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = browser.new_page(viewport={'width': 1280, 'height': 900})
        page.goto(URL, wait_until='domcontentloaded', timeout=35000)
        page.wait_for_timeout(6000)
        cards = page.query_selector_all('a[href*="/job/"]')
        jobs, seen = [], set()
        for c in cards:
            href = c.get_attribute('href') or ''
            if '/job/' not in href or href in seen:
                continue
            seen.add(href)
            j = parse_card(href, c.inner_text() or '')
            if j:
                jobs.append(j)
        browser.close()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    real = sum(1 for j in jobs if '/job/' in j.get('url', ''))
    print(f'\n✅ {len(jobs)} SN Hunt UK jobs ({real} with real /job/ URLs) → {OUT}')
    for j in jobs[:6]:
        sc_b = '🔒' if j.get('sc_clearance') else '  '
        print(f'  {sc_b} {j["title"][:50]} | {j["company"][:24]} | {j["location"]}')
    return jobs


if __name__ == '__main__':
    scrape()
