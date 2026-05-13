# ServiceNow Jobs UK — Sponsorship-Focused Job Aggregator

A daily-updated job aggregator for ServiceNow roles in the UK, cross-referenced against the UK Government sponsor register. 164 active jobs across 4 sources.

**Live site:** [ibdotboss.github.io/servicenow-jobs-digest](https://ibdotboss.github.io/servicenow-jobs-digest/)

## How It Works

Every morning at 05:00 UK time, the pipeline:
1. Scrapes **JobServe** (mobile HTML, session-based pagination)
2. Scrapes **LinkedIn** (Playwright-based, 5 pages/day with stealth delays)
3. Scrapes **Reed.co.uk** (embedded `__NEXT_DATA__` JSON)
4. Extracts **Hunt UK** (web_extract — sponsor-verified companies)
5. Cross-references all companies against the **120K sponsor register**
6. Scans job descriptions for **SC/DV clearance** and **"no sponsorship"** language
7. Saves an **immutable daily snapshot** → idempotent master rebuild

## Sponsorship Signals

| Signal | Method | Meaning |
|--------|--------|---------|
| 🟣 **Licenced** | Sponsor register CSV | Company holds A-rated Skilled Worker licence |
| 🔴 **SC-blocked** | Description text scan | Role requires SC/DV clearance (5yr UK residency) |
| 🟢 **Explicit** | Description text scan | Job explicitly mentions "visa sponsorship available" |
| ⚪ **Unknown** | — | Can't determine — treat with caution |
| 🔶 **Agency** | Source detection | Posted by recruitment agency |

**Licenced** is the primary signal. It means the company CAN sponsor — check the specific role.
**Explicit** is a data point when the text is clear, but it's rare (~5% of jobs).
No algorithm claims "verified" — that judgment is yours.

## Architecture

```
Daily pipeline (05:00 UK):
  JobServe    → jobserve_scraper.py (curl + mobile HTML)
  LinkedIn    → linkedin_job_scraper.py (Playwright + stealth)
  Reed        → sn_aggregator.py (__NEXT_DATA__ JSON)
  Hunt UK     → web_extract (sponsor search results)
       ↓
  scan_sponsorship.py (CSV cross-ref + text scan)
       ↓
  docs/data/daily/jobs_YYYY-MM-DD.json (IMMUTABLE)
       ↓
  rebuild_master.py → docs/data/master.json + jobs.json
       ↓
  GitHub Pages → index.html
```

## Scripts

| Script | Purpose |
|--------|---------|
| `jobserve_scraper.py` | JobServe mobile via session-based SHD pagination |
| `linkedin_job_scraper.py` | LinkedIn via Playwright, 5 pages/day, stealth timing |
| `sn_aggregator.py` | Reed.co.uk JSON extraction |
| `scan_sponsorship.py` | Sponsor CSV cross-ref, SC/DV and "no sponsorship" detection |
| `rebuild_master.py` | Idempotent master rebuild from immutable daily snapshots |
| `build_daily.py` | Manual daily snapshot assembly (for curation) |

## Sources

| Source | Method | Daily Yield | Notes |
|--------|--------|-------------|-------|
| JobServe | curl + mobile HTML | ~27 SN roles | No company names in mobile — shown as "via JobServe" |
| LinkedIn | Playwright + cookies | ~15 SN roles | Cookies expire ~24h, auto-harvested from Brave |
| Reed | __NEXT_DATA__ JSON | ~2 SN roles | Salary data available |
| Hunt UK | web_extract | ~8 sponsor roles | Links → LinkedIn apply pages |

**Dead sources (confirmed):** ComputerJobs (100% JobServe overlap), Indeed (Cloudflare), Totaljobs/CV-Library (JS-walled)

## Quick Start

```bash
# LinkedIn (requires manual login once)
python3 scripts/linkedin_job_scraper.py --create-session
python3 scripts/linkedin_job_scraper.py           # Daily (5 pages)
python3 scripts/linkedin_job_scraper.py --full     # Catch-up (15 pages)

# JobServe
python3 scripts/jobserve_scraper.py

# Reed + Hunt UK + Scan + Rebuild
python3 scripts/sn_aggregator.py
python3 scripts/scan_sponsorship.py --csv-only
python3 scripts/rebuild_master.py

# Deploy
git add docs/ && git commit -m "Daily update $(date +%Y-%m-%d)" && git push
```

## Cron

`0e5c2cd3fe1d` — Daily at 05:00 UK via Hermes Agent. 4 scrapers → sponsor scan → rebuild → push → Discord summary.

## License

MIT License. Copyright © 2026 Stage & Mr Faajii.
