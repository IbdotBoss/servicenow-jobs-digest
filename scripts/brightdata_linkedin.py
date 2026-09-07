#!/usr/bin/env python3
"""
Bright Data LinkedIn scraper integration (replaces dead Brave-cookie LinkedIn source).

Why this exists:
  The old linkedin_job_scraper.py depended on a live `li_at` cookie harvested from
  Brave on the VPS. That cookie died ~mid-May 2026 and cannot be revived without a
  human re-login (and the VPS datacenter IP triggers LinkedIn ID-verification).
  Bright Data's LinkedIn Scraper API scrapes public LinkedIn data WITHOUT any LinkedIn
  account — it handles proxies, anti-bot, and parsing, returning clean JSON.

Two modes:
  1. URL mode (synchronous /scrape): pass a list of LinkedIn job URLs, get structured data.
     Max 20 URLs per sync request.
  2. Discovery mode: use web_search (agent tool) or Bright Data Web Unlocker to find
     LinkedIn job URLs matching a keyword+location, then scrape via /scrape.

Output schema matches the legacy linkedin_job_scraper.py so daily_pipeline.py and
rebuild_master.py keep working:
  {title, company, location, url, source:'LinkedIn', scraped_at,
   visa_sponsorship, sponsor_licence}

Key is read from BRIGHT_DATA_API_KEY env (loaded from .env if present). Never hardcoded.

Usage:
  from brightdata_linkedin import BrightDataLinkedIn
  bd = BrightDataLinkedIn()                       # reads key from env/.env
  bd.discover(keyword='ServiceNow', location='United Kingdom')  # returns list of jobs
  # Or use the agent web_search tool for discovery, then:
  bd.scrape_urls([url1, url2])             # sync, <=20
"""
import os
import sys
import json
import time
import re
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

# ---- load .env if present (does not override real env) ----
def _load_dotenv(path=None):
    path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v

_load_dotenv()

# Canonical LinkedIn Jobs dataset (from Stage's CP config links).
LINKEDIN_JOBS_DATASET = 'gd_lpfll7v5hcqtkxl6l'
LINKEDIN_COMPANY_DATASET = 'gd_l1vikfnt1wgvvqz95w'

API_BASE = 'https://api.brightdata.com/datasets/v3'
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'docs', 'data')


class BrightDataLinkedIn:
    def __init__(self, api_key=None, verbose=True):
        self.api_key = api_key or os.environ.get('BRIGHT_DATA_API_KEY')
        self.verbose = verbose
        if not self.api_key:
            raise RuntimeError(
                "BRIGHT_DATA_API_KEY not set. Export it or add to .env "
                "(gitignored). Refusing to run without a key.")

    # ---- low-level HTTP ----
    def _post(self, endpoint, params, payload):
        url = f"{API_BASE}/{endpoint}?" + "&".join(f"{k}={v}" for k, v in params.items())
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, data=data, method='POST',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            })
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'ignore')
            return e.code, {'error': body[:500]}
        except Exception as e:  # noqa
            return 0, {'error': str(e)}

    def _get(self, endpoint, params):
        url = f"{API_BASE}/{endpoint}?" + "&".join(f"{k}={v}" for k, v in params.items())
        req = urllib.request.Request(
            url, method='GET',
            headers={'Authorization': f'Bearer {self.api_key}'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'ignore')
            return e.code, {'error': body[:500]}
        except Exception as e:  # noqa
            return 0, {'error': str(e)}

    def _unlocker_get(self, url, zone=None):
        """Fetch a URL via Bright Data Web Unlocker API (/request endpoint).

        Handles anti-bot, Cloudflare, CAPTCHAs.  Returns decoded HTML text.
        Zone name is read from BRIGHT_DATA_WEB_UNLOCKER_ZONE env var.
        Raises RuntimeError if the zone is not configured.
        """
        if zone is None:
            zone = os.environ.get('BRIGHT_DATA_WEB_UNLOCKER_ZONE', 'web_unlocker')
        unlock_url = 'https://api.brightdata.com/request'
        payload = json.dumps({
            'zone': zone,
            'url': url,
            'format': 'raw',
            'render': 'false',
        }).encode('utf-8')
        req = urllib.request.Request(unlock_url, data=payload, method='POST',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            })
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'ignore')
            raise RuntimeError(f"Unlocker API HTTP {e.code}: {body[:200]}")

    # ---- sync: scrape specific job URLs ----
    def scrape_urls(self, urls, dataset_id=LINKEDIN_JOBS_DATASET):
        if not urls:
            return []
        if len(urls) > 20:
            # split into batches of 20 (sync limit)
            out = []
            for i in range(0, len(urls), 20):
                out.extend(self.scrape_urls(urls[i:i+20], dataset_id))
            return out
        payload = [{'url': u} for u in urls]
        status, resp = self._post('scrape',
                                  {'dataset_id': dataset_id, 'format': 'json'},
                                  payload)
        if status != 200 or 'error' in resp:
            print(f"❌ scrape_urls failed ({status}): {resp.get('error', resp)}")
            return []
        return self._normalize(resp)

    # ---- discover by keyword+location ----
    def discover(self, keyword, location=None, dataset_id=LINKEDIN_JOBS_DATASET,
                 poll_interval=20, max_wait=600):
        """Discover LinkedIn jobs by keyword+location.

        Bright Data's LinkedIn Jobs dataset (gd_lpfll7v5hcqtkxl6l) only accepts
        concrete LinkedIn job URLs via /scrape — it cannot discover URLs by keyword.
        To discover jobs we:
          1. Fetch Google search results via the Bright Data Web Unlocker API
             (/request endpoint with a zone). The zone name is read from the
             BRIGHT_DATA_WEB_UNLOCKER_ZONE env var (default: 'web_unlocker').
          2. Extract linkedin.com/jobs/view/... URLs from the search page HTML.
          3. Scrape each URL via the /scrape (synchronous) endpoint.

        If the Web Unlocker zone is not configured, falls back to a direct
        urllib request (may be blocked on datacenter IPs) and ultimately
        returns [] (LinkedIn is best-effort per the pipeline spec).
        """
        query = f"site:linkedin.com/jobs/view {keyword}"
        if location:
            query += f" {location}"
        print(f"🔍 web_search: {query}")
        urls = self._find_linkedin_job_urls(query, max_results=15)
        if not urls:
            if self.verbose:
                print("  ⚠️ No LinkedIn job URLs found — LinkedIn degraded to 0 (best-effort)")
            return []

        if self.verbose:
            print(f"  Found {len(urls)} LinkedIn job URLs, scraping via Bright Data...")

        # Bright Data /scrape accepts up to 20 URLs per request
        all_jobs = []
        for i in range(0, len(urls), 20):
            batch = urls[i:i+20]
            jobs = self.scrape_urls(batch, dataset_id)
            all_jobs.extend(jobs)

        # Filter to keyword-relevant roles
        kw_lower = keyword.lower()
        filtered = [j for j in all_jobs if kw_lower in (j.get('title', '') + j.get('description', '')).lower()]
        if self.verbose:
            print(f"  ✅ discover: {len(filtered)} keyword-relevant jobs out of {len(all_jobs)} scraped")
        return filtered

    def _find_linkedin_job_urls(self, query, max_results=15):
        """Find real linkedin.com/jobs/view/... URLs.

        Tries Bright Data Web Unlocker (/request) with a configurable zone name
        first, then falls back to direct urllib.
        """
        search_url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        urls = []

        # Try Bright Data Web Unlocker with various zone names
        zone_names = [
            os.environ.get('BRIGHT_DATA_WEB_UNLOCKER_ZONE', 'web_unlocker'),
            'serp',
            'serp_api',
            'unlocker',
        ]
        for zone in zone_names:
            if not zone or zone in zone_names[:zone_names.index(zone)]:
                continue
            try:
                html = self._unlocker_get(search_url, zone=zone)
                if html and len(html) > 100:
                    urls = self._extract_linkedin_urls(html, max_results)
                    if urls:
                        return urls
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️ Web Unlocker zone='{zone}' failed: {e}")
                continue

        # Last resort: try direct urllib (may be blocked on datacenter IPs)
        if self.verbose:
            print("  ⚠️ All Web Unlocker zones failed — trying direct urllib (may be blocked)")
        try:
            req = urllib.request.Request(search_url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                html = r.read().decode('utf-8', 'ignore')
            urls = self._extract_linkedin_urls(html, max_results)
        except Exception as e:
            if self.verbose:
                print(f"  ⚠️ Direct urllib also failed: {e}")

        return urls

    @staticmethod
    def _extract_linkedin_urls(html, max_results):
        """Extract linkedin.com/jobs/view/... URLs from HTML string."""
        urls = []
        pattern = r'https?://(?:www\.)?linkedin\.com/jobs/view/[^\s"&<>\)]+'
        for m in re.finditer(pattern, html):
            u = m.group(0)
            if u not in urls:
                urls.append(u)
            if len(urls) >= max_results:
                break
        return urls

    # ---- normalize Bright Data output -> legacy schema ----
    def _normalize(self, data):
        """Accept either a list of job dicts, or {status,data:[]}, or {jobs:[]}."""
        jobs = None
        if isinstance(data, list):
            jobs = data
        elif isinstance(data, dict):
            jobs = data.get('data') or data.get('jobs') or data.get('results')
        if jobs is None:
            # maybe the whole dict IS one job
            if data and isinstance(data, dict) and data.get('title'):
                jobs = [data]
            else:
                jobs = []
        out = []
        for j in jobs:
            if not isinstance(j, dict):
                continue
            # Bright Data job fields vary; map defensively
            title = (j.get('job_title') or j.get('title') or
                     j.get('name') or '').strip()
            company = (j.get('company_name') or
                       (j.get('company') or {}).get('name') if isinstance(j.get('company'), dict)
                       else j.get('company') or '').strip()
            if isinstance(company, dict):
                company = company.get('name', '')
            location = (j.get('job_location') or j.get('location') or
                        j.get('city') or '').strip()
            url = (j.get('url') or j.get('job_url') or
                   j.get('link') or '').strip()
            if not title:
                continue
            out.append({
                'title': title,
                'company': company or 'N/A',
                'location': location or 'N/A',
                'url': url,
                'source': 'LinkedIn',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'visa_sponsorship': 'unknown',   # pipeline re-derives via scan_sponsorship
                'sponsor_licence': False,
            })
        if self.verbose:
            print(f"✅ normalized {len(out)} jobs from Bright Data response")
        return out


def main():
    """CLI probe: python3 scripts/brightdata_linkedin.py <url1> [url2 ...]"""
    bd = BrightDataLinkedIn()
    urls = sys.argv[1:]
    if not urls:
        print("Usage: python3 scripts/brightdata_linkedin.py <linkedin_job_url> [...]")
        print("Or import BrightDataLinkedIn and call .discover(keyword, location).")
        sys.exit(2)
    jobs = bd.scrape_urls(urls)
    print(json.dumps(jobs, indent=2))


if __name__ == '__main__':
    main()
