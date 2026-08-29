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
  2. Discovery mode (async /trigger): pass {keyword, location} search input so BD
     finds + scrapes matching LinkedIn jobs. Async only. Returns a snapshot_id; poll
     /progress then download from /snapshot.

Output schema matches the legacy linkedin_job_scraper.py so daily_pipeline.py and
rebuild_master.py keep working:
  {title, company, location, url, source:'LinkedIn', scraped_at,
   visa_sponsorship, sponsor_licence}

Key is read from BRIGHT_DATA_API_KEY env (loaded from .env if present). Never hardcoded.

Usage:
  from brightdata_linkedin import BrightDataLinkedIn
  bd = BrightDataLinkedIn()                       # reads key from env/.env
  jobs = bd.scrape_urls([url1, url2])             # sync, <=20
  jobs = bd.discover(keyword='ServiceNow', location='Cambridge', dataset_id=...)  # async
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
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
        # Sync /scrape returns data inline (list or {status, data})
        return self._normalize(resp)

    # ---- async: discover by keyword+location ----
    def discover(self, keyword, location=None, dataset_id=LINKEDIN_JOBS_DATASET,
                 poll_interval=20, max_wait=600):
        """Trigger an async discovery job. Returns list of normalized jobs."""
        payload = [{'keyword': keyword}]
        if location:
            payload[0]['location'] = location
        status, resp = self._post('trigger',
                                  {'dataset_id': dataset_id, 'format': 'json',
                                   'uncompressed_webhook': 'true'},
                                  payload)
        if status != 200 or 'snapshot_id' not in resp:
            print(f"❌ discover trigger failed ({status}): {resp}")
            return []
        snap = resp['snapshot_id']
        print(f"⏳ discovery triggered → snapshot_id={snap}")
        data = self._wait_snapshot(snap, poll_interval, max_wait)
        return self._normalize(data)

    def _wait_snapshot(self, snapshot_id, poll_interval, max_wait):
        waited = 0
        while waited <= max_wait:
            status, prog = self._get('progress', {'snapshot_id': snapshot_id})
            if status == 200:
                st = prog.get('status')
                if self.verbose:
                    print(f"   progress: {st} ({waited}s) — {prog.get('progress', '')}")
                if st == 'ready':
                    s2, data = self._get('snapshot', {'snapshot_id': snapshot_id})
                    if s2 == 200:
                        return data
                    print(f"❌ snapshot fetch failed ({s2}): {data}")
                    return None
                if st in ('failed', 'error'):
                    print(f"❌ snapshot {st}: {prog}")
                    return None
            time.sleep(poll_interval)
            waited += poll_interval
        print(f"⏱️ timed out after {max_wait}s waiting for snapshot {snapshot_id}")
        return None

    # ---- normalize Bright Data output → legacy schema ----
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
