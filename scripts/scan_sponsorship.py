#!/usr/bin/env python3
"""
Sponsorship scanner v2.0 — DATA, not judgment.
Scans job listings for:
  1. Sponsor licence cross-reference (company on register → sponsor_licence flag)
  2. SC/DV clearance language → visa_sponsorship = sc_blocked
  3. "No sponsorship" language → visa_sponsorship = unavailable

Does NOT output sponsor_verified or verified — that decision is manual.

Usage: python3 scripts/scan_sponsorship.py [--dry-run]
"""

import json, re, sys, os, csv, argparse
import urllib.request
from pathlib import Path
from collections import Counter
import html as htmlmod

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest")
JOBS_FILE = os.path.join(REPO, "docs/data/jobs.json")
MASTER_FILE = os.path.join(REPO, "docs/data/master.json")
SPONSOR_CSV = os.path.expanduser("~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# Patterns that mean NO sponsorship
NO_SPONSOR_PATTERNS = [
    (r'no\s+(visa\s+)?sponsorship', 'Job states no visa sponsorship'),
    (r'cannot\s+(provide\s+)?sponsor', 'Job cannot sponsor'),
    (r'unable\s+to\s+sponsor', 'Job unable to sponsor'),
    (r'does\s+not\s+(offer|provide)\s+(visa\s+)?sponsorship', 'No sponsorship offered'),
    (r'no\s+need\s+for\s+visa\s+sponsorship', 'No need for visa sponsorship'),
    (r'will\s+not\s+sponsor', 'Will not sponsor'),
    (r'(?:cannot|do\s+not)\s+(?:offer\s+)?visa\s+(?:sponsorship|sponsor)', 'Cannot offer visa sponsorship'),
    (r'this\s+(?:role|position|job)\s+(?:is\s+)?not\s+eligible\s+for\s+(?:visa\s+)?sponsorship', 'Role not eligible for sponsorship'),
]

# Patterns for SC/DV clearance (blocks sponsorship)
SC_PATTERNS = [
    (r'(?:security\s+(?:clearance|cleared)|sc\s+clear|sc\s+cleared|dv\s+clear|dv\s+cleared|developed\s+vetting)', 'Security clearance required'),
    (r'must\s+be\s+eligible\s+for\s+(?:\w+\s+)?(?:sc|security)\s+clearance', 'SC clearance eligibility required'),
    (r'5\s+years?\s+(?:continuous\s+)?uk\s+residency', '5yr UK residency required'),
    (r'sc\s+(?:clearance|cleared)\s+(?:is\s+)?(?:required|essential|mandatory|needed)', 'SC clearance mandatory'),
    (r'bpss\s+(?:clearance|check)', 'BPSS clearance required'),
]

def load_sponsor_set():
    """Load A-rated Skilled Worker sponsors from CSV → set of normalized company names."""
    if not os.path.exists(SPONSOR_CSV):
        print(f"[WARN] Sponsor CSV not found: {SPONSOR_CSV}")
        return set()
    
    sponsors = set()
    try:
        with open(SPONSOR_CSV, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                route = row.get('Route', '').lower()
                rating = row.get('Type & Rating', '').lower()
                name = row.get('Organisation Name', '').strip()
                if name and 'skilled worker' in route and 'a rating' in rating:
                    # Normalize: lowercase, strip common suffixes
                    normalized = name.lower().strip()
                    sponsors.add(normalized)
        print(f"[INFO] Loaded {len(sponsors)} A-rated Skilled Worker sponsors")
    except Exception as e:
        print(f"[ERROR] Failed to load sponsor CSV: {e}")
    
    return sponsors

def normalize_company(name):
    """Normalize company name for fuzzy matching against sponsor register."""
    if not name:
        return ''
    n = name.lower().strip()
    # Strip common legal suffixes
    for suffix in [' ltd', ' limited', ' plc', ' uk limited', ' uk', ' (uk)', '(uk)',
                   ' corporation', ' inc', ' incorporated', ' group', ' holdings',
                   ' services', ' solutions', ' technologies', ' consulting']:
        if n.endswith(suffix):
            n = n[:-len(suffix)].strip()
    # Strip parenthetical qualifiers
    import re as re_mod
    n = re_mod.sub(r'\s*\([^)]*\)\s*', ' ', n).strip()
    # Strip trailing qualifiers after dash
    if ' - ' in n:
        n = n.split(' - ')[0].strip()
    return n

# Company names that should NEVER match the sponsor register,
# even if a substring happens to appear in the CSV.
# Pitfall #51: literal "Agency" matches CSV entries like "Agency X Ltd"
# Pitfall #53: recruitment agencies post on behalf of clients — the
#   agency's licence doesn't apply to the end employer.
COMPANY_NAME_BLACKLIST = {
    'agency', '[view listing]', 'confidential', 'unknown', '', 'none',
}

AGENCY_KEYWORDS = [
    'recruitment', 'recruiting', 'staffing', 'personnel',
    'talent solutions', 'resource solutions',
]

# Well-known recruitment agencies whose sponsor licence
# doesn't transfer to the actual employer they're posting for.
KNOWN_AGENCIES = {
    'hays', 'harvey nash', 'sthree', 'randstad', 'randstad technologies', 'adecco',
    'michael page', 'robert walters', 'morgan mckinley',
    'huxley', 'teksystems', 'la fose', 'la fosse',
    'sanderson', 'harvey nash limited', 'hays recruitment',
    'e-team', 'eteam', 'gios technology', 'morson talent', 'morson',
    'coyle personnel', 'explain recruitment',
}

def is_agency(company_name):
    """Check if company name indicates a recruitment agency."""
    if not company_name:
        return False
    name_lower = company_name.lower().strip()
    # Explicit agency marker
    if '(agency)' in name_lower:
        return True
    # Via pattern: "Barclays via SThree" → SThree is the agency
    if ' via ' in name_lower:
        return True
    # Keyword match
    for kw in AGENCY_KEYWORDS:
        if kw in name_lower:
            return True
    # Known agency normalized match
    norm = name_lower
    # Strip parenthetical qualifiers: "SThree (banking client)" → "SThree"
    norm = re.sub(r'\s*\([^)]*\)\s*', ' ', norm).strip()
    for suffix in [' (agency)', ' ltd', ' limited', ' plc', ' uk limited', ' uk',
                   ' technologies', ' consulting', ' solutions', ' services',
                   ' personnel', ' talent', ' recruitment']:
        if norm.endswith(suffix):
            norm = norm[:-len(suffix)].strip()
    if norm in KNOWN_AGENCIES:
        return True
    return False

def company_has_licence(company_name, sponsor_set):
    """Check if company appears in sponsor set (exact match + fuzzy fallback).
    
    Returns (bool, str) — (has_licence, reason).
    Blacklisted names and agencies are blocked even if they match the CSV.
    """
    if not company_name or not sponsor_set:
        return False, ''
    
    raw = company_name.lower().strip()
    
    # ── Negative filter: blacklisted company names ──
    if raw in COMPANY_NAME_BLACKLIST:
        return False, f'blacklisted_name:{raw}'
    
    # ── Negative filter: likely recruitment agency ──
    if is_agency(company_name):
        return False, f'agency_name:{raw}'
    
    # Exact match first
    if raw in sponsor_set:
        return True, 'exact'
    
    # Normalized match
    norm = normalize_company(company_name)
    if norm and norm in sponsor_set:
        return True, 'normalized'
    
    # Partial match: check if any sponsor contains the normalized name or vice-versa
    if norm and len(norm) > 2:
        for s in sponsor_set:
            if norm in s or s in norm:
                return True, 'partial'
    
    return False, ''

def fetch_page(url):
    """Fetch job listing page. Returns (html_text, error)."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        resp = urllib.request.urlopen(req, timeout=15)
        raw = resp.read().decode('utf-8', errors='ignore')
        return htmlmod.unescape(raw), None
    except Exception as e:
        return '', str(e)

# Patterns that explicitly CONFIRM sponsorship (mentioned in description)
SPONSOR_MENTIONED_PATTERNS = [
    (r'visa\s+sponsorship\s+(?:can\s+be\s+)?(?:provided|available|offered)', 'Visa sponsorship mentioned in description'),
    (r'sponsorship\s+(?:is\s+)?(?:available|provided|offered)', 'Sponsorship mentioned'),
    (r'skilled\s+worker\s+visa', 'Skilled Worker visa mentioned'),
    (r'(?:we\s+(?:can|will|offer|provide)\s+(?:visa\s+)?sponsorship)', 'We can sponsor'),
]

def scan_text(text):
    """Scan HTML text for sponsorship language. Returns (tag, reason) or (None, None)."""
    text_lower = text.lower()
    
    # Check SC/DV first (strongest signal) — also match title-level patterns
    for pattern, reason in SC_PATTERNS:
        if re.search(pattern, text_lower):
            return 'sc_blocked', reason
    # Extra title-level checks that the page-text patterns might miss
    extra_sc = [
        'sc security clearance', 'security clearance required',
        'must be security cleared', 'active security clearance',
        'security cleared', 'security cleared ',
    ]
    for pat in extra_sc:
        if pat in text_lower:
            return 'sc_blocked', f'Title mentions: {pat}'
    
    # Check NO patterns
    for pattern, reason in NO_SPONSOR_PATTERNS:
        if re.search(pattern, text_lower):
            return 'unavailable', reason
    
    return None, None

def scan_job(job, sponsor_set):
    """Scan a single job. Returns dict of { field: value } updates."""
    updates = {}
    url = job.get('url', '')
    source = job.get('source', '').lower()
    company = job.get('company', '')
    current_sp = job.get('visa_sponsorship', 'unknown')
    description = job.get('description', '')
    
    # ── Step 1: Sponsor licence check ──
    if company and sponsor_set:
        has_licence, _reason = company_has_licence(company, sponsor_set)
        if has_licence:
            updates['sponsor_licence'] = True
        elif job.get('sponsor_licence'):
            # Previously tagged but now blocked (agency/blacklist) → strip it
            updates['sponsor_licence'] = False
    
    # ── Step 1.5: Title-level SC/DV check (always, even for LinkedIn) ──
    title = job.get('title', '')
    if title:
        tag, reason = scan_text(title)
        if tag:
            updates['visa_sponsorship'] = tag
            updates['sponsorship_scan'] = reason
    
    # ── Step 2: Text scan ──
    # LinkedIn job pages are JS-rendered — can't fetch full page
    # But some have description text from Voyager API
    if 'linkedin.com/jobs/view' in url or source == 'linkedin':
        # Try scanning the description field (may have brief text)
        if description and len(description) > 50:
            tag, reason = scan_text(description)
            if tag:
                updates['visa_sponsorship'] = tag
                updates['sponsorship_scan'] = reason
            # Also check for "no sponsorship" in description from Voyager
            for pattern, reason in NO_SPONSOR_PATTERNS:
                if re.search(pattern, description.lower()):
                    updates['visa_sponsorship'] = 'unavailable'
                    updates['sponsorship_scan'] = reason
                    break
        else:
            updates['sponsorship_scan'] = 'linkedin_js (cannot read full description)'
        return updates
    
    # Skip if no URL
    if not url or url in ['', 'https://']:
        return updates
    
    # Fetch and scan the actual page
    html_text, error = fetch_page(url)
    if error:
        updates['sponsorship_scan'] = f'fetch_error: {error[:60]}'
        return updates
    
    if len(html_text) < 500:
        updates['sponsorship_scan'] = f'page_too_short ({len(html_text)} chars)'
        return updates
    
    tag, reason = scan_text(html_text)
    if tag:
        updates['visa_sponsorship'] = tag
        updates['sponsorship_scan'] = reason
    
    # Also check for explicit sponsorship mention (data point, not a tag)
    if company and sponsor_set:
        has_licence, _ = company_has_licence(company, sponsor_set)
        if has_licence:
            for pattern, _ in SPONSOR_MENTIONED_PATTERNS:
                if re.search(pattern, html_text.lower()):
                    updates['sponsorship_mentioned'] = True
                    break
    
    return updates

def scan_file(filepath, sponsor_set, dry_run=False, csv_only=False):
    """Scan all jobs in a JSON file and apply updates.
    csv_only=True: skip page fetching, only do sponsor CSV lookup."""
    with open(filepath) as f:
        data = json.load(f)
    
    if isinstance(data, list):
        jobs = data
    elif isinstance(data, dict) and 'jobs' in data:
        jobs = data['jobs']
    else:
        jobs = []
    was_list = isinstance(data, list)
    
    changes = {'sc_blocked': 0, 'unavailable': 0, 'licence_flagged': 0}
    
    for j in jobs:
        current_sp = j.get('visa_sponsorship', 'unknown')
        current_licence = j.get('sponsor_licence', False)
        
        if csv_only:
            # Just the sponsor CSV lookup
            updates = {}
            company = j.get('company', '')
            if company and sponsor_set:
                has_licence, _reason = company_has_licence(company, sponsor_set)
                if has_licence:
                    updates['sponsor_licence'] = True
                elif j.get('sponsor_licence'):
                    updates['sponsor_licence'] = False
        else:
            updates = scan_job(j, sponsor_set)
        
        # Apply updates
        for key, value in updates.items():
            j[key] = value
        
        # Track changes
        if 'visa_sponsorship' in updates and updates['visa_sponsorship'] != current_sp:
            changes[updates['visa_sponsorship']] = changes.get(updates['visa_sponsorship'], 0) + 1
        if 'sponsor_licence' in updates and updates['sponsor_licence'] != current_licence:
            changes['licence_flagged'] += 1
    
    # Recount totals
    tags = Counter(j.get('visa_sponsorship', 'unknown') for j in jobs)
    licence_count = sum(1 for j in jobs if j.get('sponsor_licence'))
    
    if not dry_run and any(changes.values()):
        data['sc_blocked'] = tags.get('sc_blocked', 0)
        data['verified'] = tags.get('verified', 0) + tags.get('sponsor_verified', 0)
        if 'daily_snapshots' in data:  # master.json has this key
            data['licenced_sponsors'] = licence_count
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    return changes, tags, licence_count

def main(dry_run=False, csv_only=False, file_path=None, skip_defaults=False):
    sponsor_set = load_sponsor_set()
    if not sponsor_set:
        print("[ERROR] No sponsor data loaded — aborting. Check CSV path.")
        sys.exit(1)
    
    mode = "CSV-only" if csv_only else "full (with page fetching)"
    files_to_scan = []
    if file_path:
        files_to_scan.append(file_path)
    if not skip_defaults:
        files_to_scan.extend([JOBS_FILE, MASTER_FILE])
    
    total_changes = {'sc_blocked': 0, 'unavailable': 0, 'licence_flagged': 0}
    total_tags = Counter()
    total_licence = 0
    
    for fp in files_to_scan:
        print(f"Scanning {fp} ({mode})...")
        changes, tags, licence_count = scan_file(fp, sponsor_set, dry_run, csv_only)
        print(f"  Tags: {dict(tags.most_common())}")
        print(f"  Companies with sponsor licence: {licence_count}")
        print(f"  Changes: {changes}")
        for k in total_changes:
            total_changes[k] += changes.get(k, 0)
        total_tags.update(tags)
        total_licence += licence_count
    
    total_ver = total_tags.get('verified', 0) + total_tags.get('sponsor_verified', 0)
    total_sc = total_tags.get('sc_blocked', 0)
    total_unavail = total_tags.get('unavailable', 0)
    total_agency = total_tags.get('agency_unknown', 0)
    
    print(f"\nSummary: {sum(total_tags.values())} total jobs")
    print(f"  Verified (manual): {total_ver}")
    print(f"  SC-blocked (auto): {total_sc}")
    print(f"  Unavailable (auto): {total_unavail}")
    print(f"  Agency (manual): {total_agency}")
    print(f"  Unknown: {total_tags.get('unknown', 0)}")
    print(f"  Companies with sponsor licence: {total_licence}")
    
    if dry_run:
        print("\n[DRY RUN] No files written.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--csv-only', action='store_true',
                        help='Skip page fetching — only cross-reference sponsor CSV')
    parser.add_argument('--file', help='Scan a specific JSON file (in addition to defaults)')
    parser.add_argument('--skip-defaults', action='store_true',
                        help='Skip scanning jobs.json and master.json')
    args = parser.parse_args()
    main(dry_run=args.dry_run, csv_only=args.csv_only, file_path=args.file, skip_defaults=args.skip_defaults)
