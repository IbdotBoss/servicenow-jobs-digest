#!/usr/bin/env python3
"""
Sponsorship language scanner for job listings.
Scans job detail pages for sponsorship/SC/residency language.
Returns updated visa_sponsorship tag.

Usage: python3 scripts/scan_sponsorship.py [--dry-run]
"""

import json, re, sys, os, argparse
import urllib.request
from pathlib import Path
import html as htmlmod

JOBS_FILE = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobs.json")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# Patterns that mean NO sponsorship
NO_SPONSOR_PATTERNS = [
    (r'no\s+(visa\s+)?sponsorship', 'NO_SPONSORSHIP', 'Job states no visa sponsorship'),
    (r'cannot\s+(provide\s+)?sponsor', 'NO_SPONSORSHIP', 'Job cannot sponsor'),
    (r'unable\s+to\s+sponsor', 'NO_SPONSORSHIP', 'Job unable to sponsor'),
    (r'does\s+not\s+(offer|provide)\s+(visa\s+)?sponsorship', 'NO_SPONSORSHIP', 'No sponsorship offered'),
    (r'no\s+need\s+for\s+visa\s+sponsorship', 'NO_SPONSORSHIP', 'No need for visa sponsorship'),
    (r'will\s+not\s+sponsor', 'NO_SPONSORSHIP', 'Will not sponsor'),
]

# Patterns that mean RIGHT-TO-WORK required (effectively blocks sponsorship)
RTW_PATTERNS = [
    (r'must\s+have\s+(the\s+)?right\s+to\s+work', 'RTW_REQUIRED', 'Must have right to work'),
    (r'must\s+already\s+have\s+(the\s+)?right\s+to\s+work', 'RTW_REQUIRED', 'Must already have right to work'),
    (r'must\s+be\s+eligible\s+to\s+work\s+in\s+the\s+uk', 'RTW_REQUIRED', 'Must be eligible to work in UK'),
    (r'right\s+to\s+work\s+in\s+the\s+uk', 'RTW_HINT', 'Right to work in UK mentioned'),
]

# Patterns for SC/DV clearance (blocks sponsorship)
SC_PATTERNS = [
    (r'(?:security\s+clearance|sc\s+clear|sc\s+cleared|dv\s+clear|dv\s+cleared|developed\s+vetting)', 'SC_REQUIRED', 'Security clearance required'),
    (r'must\s+be\s+eligible\s+for\s+(?:sc|security)\s+clearance', 'SC_REQUIRED', 'SC clearance eligibility required'),
    (r'5\s+years?\s+(?:continuous\s+)?uk\s+residency', 'SC_RESIDENCY', '5yr UK residency required'),
    (r'sc\s+(?:clearance|cleared)\s+(?:is\s+)?(?:required|essential|mandatory|needed)', 'SC_REQUIRED', 'SC clearance mandatory'),
]

# Patterns that CONFIRM sponsorship
YES_SPONSOR_PATTERNS = [
    (r'visa\s+sponsorship\s+(?:is\s+)?available', 'SPONSOR_CONFIRMED', 'Visa sponsorship available'),
    (r'sponsorship\s+(?:is\s+)?available', 'SPONSOR_CONFIRMED', 'Sponsorship available'),
    (r'we\s+(?:can|will|offer|provide)\s+(?:visa\s+)?sponsor', 'SPONSOR_CONFIRMED', 'Sponsorship offered'),
    (r'skilled\s+worker\s+visa', 'SPONSOR_CONFIRMED', 'Skilled Worker visa mentioned'),
    (r'tier\s+2\s+(?:visa|sponsor)', 'SPONSOR_CONFIRMED', 'Tier 2 visa sponsorship'),
    (r'(?:provide|offer)\s+visa\s+sponsorship', 'SPONSOR_CONFIRMED', 'Visa sponsorship provided'),
]

def fetch_page(url, source=''):
    """Fetch job listing page. Returns (html_text, error)."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        resp = urllib.request.urlopen(req, timeout=15)
        raw = resp.read().decode('utf-8', errors='ignore')
        return htmlmod.unescape(raw), None
    except Exception as e:
        return '', str(e)

def scan_text(text):
    """Scan HTML text for sponsorship language. Returns (tag, reason)."""
    text_lower = text.lower()
    
    # Check NO patterns first (strongest signal)
    for pattern, tag, reason in NO_SPONSOR_PATTERNS:
        if re.search(pattern, text_lower):
            return 'unavailable', reason
    
    # Check SC/DV
    for pattern, tag, reason in SC_PATTERNS:
        if re.search(pattern, text_lower):
            return 'sc_blocked', reason
    
    # Check RTW
    for pattern, tag, reason in RTW_PATTERNS:
        if re.search(pattern, text_lower):
            if tag == 'RTW_REQUIRED':
                return 'unavailable', reason
            return 'rtw_check_needed', reason
    
    # Check YES patterns
    for pattern, tag, reason in YES_SPONSOR_PATTERNS:
        if re.search(pattern, text_lower):
            return 'sponsor_verified', reason
    
    return None, None

def scan_job(job):
    """Scan a single job listing. Returns (new_tag, reason)."""
    url = job.get('url', '')
    source = job.get('source', '').lower()
    current_tag = job.get('visa_sponsorship', 'unknown')
    
    # Skip jobs we can't scan (LinkedIn detail pages are JS-rendered)
    if 'linkedin.com/jobs/view' in url:
        # LinkedIn: we can't scan detail pages (JS-rendered)
        # But we keep the register-based tag
        return None, f'linkedin_js_cannot_scan (register_tag={current_tag})'
    
    # Skip if no URL
    if not url:
        return None, 'no_url'
    
    # Fetch and scan
    html_text, error = fetch_page(url)
    if error:
        return None, f'fetch_error: {error[:60]}'
    
    if len(html_text) < 500:
        return None, f'page_too_short ({len(html_text)} chars)'
    
    tag, reason = scan_text(html_text)
    return tag, reason

def main(dry_run=False):
    with open(JOBS_FILE) as f:
        data = json.load(f)
    
    jobs = data['jobs']
    changes = []
    skipped = 0
    
    for j in jobs:
        current = j.get('visa_sponsorship', 'unknown')
        url = j.get('url', '')
        
        tag, reason = scan_job(j)
        
        if tag and tag != current:
            old_tag = current
            j['visa_sponsorship'] = tag
            j['sponsorship_scan'] = reason
            changes.append((j['title'][:60], j['company'], old_tag, tag, reason))
        elif reason and reason.startswith('linkedin_js'):
            skipped += 1
        elif reason and reason not in ('no_url',):
            # Just record the scan
            j['sponsorship_scan'] = reason
    
    if not dry_run and changes:
        # Recount
        from collections import Counter
        tags = Counter(j['visa_sponsorship'] for j in jobs)
        data['verified'] = tags.get('sponsor_verified', 0) + tags.get('verified', 0)
        data['sc_blocked'] = tags.get('sc_blocked', 0)
        
        with open(JOBS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    print(f"Total jobs: {len(jobs)}")
    print(f"Changes made: {len(changes)}")
    print(f"LinkedIn skipped (JS): {skipped}")
    print()
    
    if changes:
        print("=== CHANGES ===")
        for title, company, old, new, reason in changes:
            print(f"  {old:20s} → {new:20s} | {title[:50]}")
            print(f"    {company} | {reason}")
            print()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    main(dry_run=args.dry_run)
