#!/usr/bin/env python3
"""LinkedIn job search through the public guest endpoint. No account, no cookies.

    linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search

Returns 10 cards per page with title, company, location, URL and the real
posting date (<time datetime>), which Bright Data never gave us. Shared by the
digest (daily_pipeline.py) and the private faaja-jobs shortlist, which imports
this file from here, so keep the search() signature stable.

    python3 scripts/linkedin_guest.py "servicenow analyst" --entry
"""
import html, re, subprocess, sys, time, random
from urllib.parse import urlencode

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
BASE = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
CARD = re.compile(r'<li>(.*?)</li>', re.S)


def _text(pattern, block):
    m = re.search(pattern, block, re.S)
    return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''


def parse(page):
    jobs = []
    for block in CARD.findall(page):
        jid = re.search(r'urn:li:jobPosting:(\d+)', block)
        title = _text(r'base-search-card__title">(.*?)</h3>', block)
        if not jid or not title:
            continue
        date = re.search(r'<time[^>]*datetime="([\d-]+)"', block)
        jobs.append({
            'title': title,
            'company': _text(r'base-search-card__subtitle">(.*?)</h4>', block) or 'Unknown',
            'location': _text(r'job-search-card__location">(.*?)</span>', block),
            'url': f'https://www.linkedin.com/jobs/view/{jid.group(1)}/',
            'date_posted': date.group(1) if date else '',
            'source': 'LinkedIn',
        })
    return jobs


def search(keywords, location='United Kingdom', days=7, entry=False, remote=False,
           pages=2, delay=(3, 5)):
    """entry=True keeps internship + entry level (f_E=1,2). remote=True: remote only."""
    params = {'keywords': keywords, 'location': location, 'f_TPR': f'r{days * 86400}'}
    if entry:
        params['f_E'] = '1,2'
    if remote:
        params['f_WT'] = '2'
    out, seen = [], set()
    for p in range(pages):
        params['start'] = p * 10
        r = subprocess.run(['curl', '-s', '-A', UA, '--max-time', '20',
                            '-w', '\n%{http_code}', f'{BASE}?{urlencode(params)}'],
                           capture_output=True, text=True)
        body, _, code = r.stdout.rpartition('\n')
        if code != '200':
            print(f'  LinkedIn guest HTTP {code} for "{keywords}" page {p}', file=sys.stderr)
            break
        batch = [j for j in parse(body) if j['url'] not in seen]
        seen.update(j['url'] for j in batch)
        out += batch
        if len(batch) < 10:
            break
        time.sleep(random.uniform(*delay))
    return out


if __name__ == '__main__':
    for j in search(sys.argv[1], entry='--entry' in sys.argv, remote='--remote' in sys.argv):
        print(f"{j['date_posted']}  {j['title'][:50]:50s} | {j['company'][:28]:28s} | {j['location']}")
