# ServiceNow Jobs UK — Sponsorship-Verified Roles

A daily-updated job aggregator for ServiceNow roles in the UK, specifically filtering for visa sponsorship eligibility. Built with zero Playwright dependencies — lightweight, terminal-friendly scrapers.

**Live site:** https://ibdotboss.github.io/servicenow-jobs-digest/

## 🚀 Features

- **95+ active ServiceNow UK jobs** from 4+ sources
- **Sponsorship tagging**: `verified` (sponsor-licensed employer), `sc_blocked` (clearance required), `agency_unknown` (recruitment agency), `unavailable` (explicitly no sponsorship)
- **Daily cron** at 05:00 UK — auto-scrapes, merges, deploys
- **Files-per-day architecture** — immutable daily snapshots, idempotent master rebuild
- **Canonical Apply links** — working direct-to-job URLs (no generic search pages)
- **Filter by**: sponsorship status, role type, source, SC clearance
- **Date selector** — browse any historical snapshot

## 📋 Architecture

```
Daily scrape (05:00 UK via Hermes cron):
  JobServe mobile  → jobserve_scraper.py (session-based SHD pagination)
  LinkedIn         → linkedin_job_scraper.py (Playwright, stealth, 5 pages/day)
  Reed.co.uk       → sn_aggregator.py (__NEXT_DATA__ JSON)
  Hunt UK          → web_extract
       ↓
  Save IMMUTABLE snapshot → docs/data/daily/jobs_YYYY-MM-DD.json
       ↓
  rebuild_master.py (idempotent — reads ALL daily files, dedupes, computes status)
       ↓
  master.json ← full archive (first_seen, last_seen, status)
  jobs.json   ← active-only copy for index page
       ↓
  GitHub Pages → index.html (date selector + active jobs)
```

## 🔧 Scrapers

| Source | Method | Yield | Notes |
|--------|--------|-------|-------|
| **JobServe** | `curl` → mobile HTML → session-based SHD | ~27 SN roles | ⚠️ No company names in mobile listings. Canonical permalink extracted from detail pages. |
| **LinkedIn** | `linkedin-job-scraper` (Playwright + real browser) | ~59 SN roles | Uses saved session file. 5 pages/day with 3-5s delays. |
| **Reed.co.uk** | `__NEXT_DATA__` JSON extraction | ~2-5 SN roles | Salary data available. |
| **Hunt UK** | `web_extract` search + role pages | ~8 verified sponsors | Links expire fast (410 Gone). Use as trust signals. |

### Dead sources (confirmed)
- **ComputerJobs** — 100% JobServe overlap (same backend engine)
- **Indeed** — Cloudflare walled (403)
- **Totaljobs/CV-Library** — JS-walled
- **Deerfoot** — Generic landing page, no specific job links

## 🏷️ Sponsorship Tags (FIVE states)

| Tag | Meaning |
|-----|---------|
| `verified` | Company is A-rated on sponsor register AND job description doesn't say "no sponsorship" |
| `sc_blocked` | Company has licence but requires Security Check/DV (5yr UK residency needed) |
| `agency_unknown` | Posted by recruitment agency — verify sponsorship with actual employer |
| `unavailable` | Listing explicitly states no visa sponsorship available |
| `unknown` | Cannot determine — treat with caution |

## 🔑 Key Files

```
servicenow-jobs-digest/
├── scripts/
│   ├── jobserve_scraper.py      # JobServe mobile scraper (session-based SHD)
│   ├── linkedin_job_scraper.py   # Playwright-based LinkedIn scraper (stealth)
│   ├── sn_aggregator.py          # Reed + Hunt UK + sponsor CSV cross-ref
│   ├── scan_sponsorship.py       # Listing-level sponsorship verification
│   └── rebuild_master.py         # Idempotent master rebuild from daily files
├── docs/
│   ├── index.html                # Dynamic dashboard (inline CSS + JS)
│   ├── data/
│   │   ├── master.json           # Full archive (all jobs, all dates)
│   │   ├── jobs.json             # Active-only copy
│   │   └── daily/                # Immutable daily snapshots
│   └── daily/
│       └── jobs_YYYY-MM-DD.json  # Self-contained daily view
└── README.md
```

## 🚦 Cron

`0e5c2cd3fe1d` — Daily at 05:00 UK via Hermes Agent. Pipeline steps:
1. JobServe scrape → session-based SHD pagination
2. LinkedIn scrape → Playwright, stealthy, 5 pages
3. Reed + Hunt UK → __NEXT_DATA__ + web_extract
4. Sponsorship scanner → listing-level check
5. Save daily snapshot (immutable)
6. Rebuild master.json (idempotent)
7. Push to GitHub Pages

## 🐞 Known Issues

- **JobServe mobile listings lack company names** — extracted from detail pages in post-processing
- **LinkedIn requires manual session creation** — run `python3 scripts/linkedin_job_scraper.py --create-session`
- **Hunt UK links expire (410 Gone)** — use as trust signals, not Apply links
- **SC/DV clearance = sponsorship killer** — 5 years continuous UK residency required

## 📄 License

MIT License. Copyright © 2026 Stage & Mr Faajii.
