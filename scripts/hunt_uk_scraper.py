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

Output: data/hunt_uk_jobs.json
"""

import json, os, re, glob as _g, sys
from datetime import datetime
from urllib.parse import urljoin

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. pip3 install playwright && playwright install chromium")
    sys.exit(1)

URL = 'https://huntukvisasponsors.com/jobs?q=servicenow'
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'hunt_uk_jobs.json')
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
# Hunt UK's own sponsorship verdict badge on each card
BADGE_RE = re.compile(r'^(likely|unlikely|high|medium|low|ineligible)$', re.IGNORECASE)


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
    """Parse a Hunt UK job card.

    CARD LAYOUT (observed 2026-10-12): each job emits TWO anchors that share one
    href — one wrapping the title, one wrapping the sponsorship badge ('Likely').
    The company and location are NOT inside the title anchor; they live only in
    the badge anchor's parent container, which renders the full card:

        ServiceNow CSM Principal Engineer
        The Boston Consulting Group UK LLP
        London, United Kingdom
        Likely
        Full-time
        —
        3d ago

    So we parse the anchor's parentElement text (the card), not the anchor text.
    Reading only the anchor text yields company='Unknown' for every job, which
    is exactly the v2.4 → today regression this fixes.
    """
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    lines = [l for l in lines if l.lower() not in TOKENS]
    if not lines:
        return None

    title = lines[0]
    if not ROLE_KW.search(title):
        return None

    # Walk the remaining lines and classify by shape rather than by fixed index.
    # Title is lines[0]; the following lines are company / location / badge /
    # employment-type / separator / age, in that order but not guaranteed.
    company = 'Unknown'
    location = 'United Kingdom'
    badge = ''
    posted = ''
    rest = lines[1:]

    # Company: the first line after the title that is not a UK location,
    # not a badge, and not a relative-age string.
    for l in rest:
        low = l.lower()
        if BADGE_RE.match(l) or low in ('—', '-', '|', 'full-time', 'part time',
                                        'part-time', 'contract', 'temporary'):
            continue
        if UK_RE.search(l) and re.search(r',', l):
            continue  # looks like "London, United Kingdom" — a location line
        if re.search(r'\d+\s*(?:d|day|h|hour|w|week|mo|month)\s*ago', low) \
                or low in ('just now', 'today', 'new'):
            continue
        if 'LIMITED' in l.upper() or 'LTD' in l.upper() or l.lower().startswith('at '):
            company = l
            break
        company = l
        break

    # Location: first UK-matching line that isn't the company line. A company
    # name can match UK_RE on its own ("The Boston Consulting Group UK LLP"),
    # so require a comma (city, country) or an exact place-only line.
    location = 'United Kingdom'
    for l in rest:
        if l == company:
            continue
        if 'LIMITED' in l.upper() or 'LTD' in l.upper() or 'LLP' in l.upper():
            continue
        if UK_RE.search(l) and (re.search(r',', l) or len(l.split()) <= 3):
            location = l.rstrip('—').strip() or 'United Kingdom'
            break

    # Hunt UK's own sponsorship verdict — a real signal we were discarding.
    for l in rest:
        if BADGE_RE.match(l):
            badge = l.lower()
            break

    # Posted date (card shows relative age; kept for display only).
    for l in rest:
        low = l.lower()
        if re.search(r'\d+\s*(?:d|day|h|hour|w|week|mo|month)\s*ago', low) \
                or low in ('just now', 'today'):
            posted = l
            break

    # Fallback: if the parent text gave us nothing usable, try the slug.
    # Slugs embed the employer as "...-at-deloitte-ssxh-c1qhhu"; the trailing
    # segments are a short hash, so require a meaningful length before use.
    if company == 'Unknown':
        m = re.search(r'-at-([a-z0-9-]+?)-[a-z0-9]{4,}(?:-[a-z0-9]{4,})?$', href)
        if m:
            slug_co = m.group(1).replace('-', ' ').strip()
            # Reject hash fragments like 'ssxh' — keep only multi-word or
            # longer-than-hash candidates.
            if len(slug_co) >= 5 and not re.fullmatch(r'[a-z]{4,6}', slug_co):
                company = slug_co.title()

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
        'sponsor_likelihood_badge': badge,
        'posted_relative': posted,
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
        # SINGLE DOM PASS. Each job card emits two anchors sharing one href
        # (title + sponsorship badge). Rather than guess per-anchor, walk the
        # closest element that CONTAINS a comma-location line — that is the card
        # container — and capture its text once per href.
        card_data = page.evaluate("""() => {
            const out = {};
            const anchors = Array.from(document.querySelectorAll('a[href*="/job/"]'));
            for (const a of anchors) {
                const href = a.getAttribute('href') || '';
                if (!href.includes('/job/')) continue;
                // climb until the text has >=4 lines (title + company + loc + badge)
                let node = a, best = '';
                for (let d = 0; d < 5 && node; d++, node = node.parentElement) {
                    const t = node.innerText || '';
                    if (t.split('\\n').filter(s => s.trim()).length >= 4) { best = t; break; }
                    if (t.length > best.length) best = t;
                }
                if (!best) best = a.innerText || '';
                if (!out[href] || best.length > out[href].length) out[href] = best;
            }
            return out;
        }""")
        jobs, seen = [], set()
        for href_raw, card_text in card_data.items():
            href = href_raw
            # FIX: Hunt UK emits relative URLs (/job/...) — resolve to absolute so
            # the sponsorship scanner can fetch the page for SC/DV text scanning.
            # Relative URLs cause fetch_error: unknown url type: '/job/...'
            if href.startswith('/job/'):
                href = urljoin('https://huntukvisasponsors.com', href)
            if href in seen:
                continue
            j = parse_card(href, card_text)
            if not j:
                continue
            seen.add(href)
            jobs.append(j)
        browser.close()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    real = sum(1 for j in jobs if '/job/' in j.get('url', ''))
    named = sum(1 for j in jobs if j.get('company') not in ('Unknown', '', None))
    print(f'\n✅ {len(jobs)} SN Hunt UK jobs ({real} with real /job/ URLs, '
          f'{named} with company names) → {OUT}')
    for j in jobs[:6]:
        sc_b = '🔒' if j.get('sc_clearance') else '  '
        badge = j.get('sponsor_likelihood_badge') or '-'
        print(f'  {sc_b} {j["title"][:44]:44s} | {j["company"][:26]:26s} '
              f'| {j["location"][:26]:26s} | {badge}')
    return jobs


if __name__ == '__main__':
    scrape()
