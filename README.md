# ServiceNow Jobs UK

Open ServiceNow roles in the UK, collected every morning, with each employer checked against the Home Office register of licensed visa sponsors.

**Site:** https://ibdotboss.github.io/servicenow-jobs-digest/

It answers one question for people who need a visa to work in the UK: which of today's ServiceNow roles are at an employer that can sponsor one. Everyone else gets a plain, searchable list of ServiceNow work.

## What the sponsorship column means

| Label | What was checked |
|---|---|
| Licensed sponsor | The employer's name matches an A-rated Skilled Worker sponsor on the register. |
| No register match | The name wasn't found. The employer may be registered under a different name. |
| Needs SC or DV clearance | The listing asks for security clearance, which has UK residence requirements. |
| Agency | A recruiter posted the role and the employer isn't named. A recruiter's licence doesn't cover its clients. |
| No sponsorship | The listing says it won't sponsor. |

A licensed employer *can* sponsor. That doesn't mean it will for a given role, so check the listing.

Names are matched whole, after dropping endings like Ltd, PLC and UK. "IBM UNITED KINGDOM LIMITED" matches "IBM UK Ltd". "TXP" does not match "Gadgetxperts Limited". Until October 2026 the match was by substring, and that produced false badges like the TXP one.

## How it runs

A scheduled job on a small VPS runs `daily_cron.sh` at 05:00 UTC. That runs `scripts/daily_pipeline.py`, which does this in order:

1. **Scrape.** JobServe (mobile pages), LinkedIn (the public guest search), Hunt UK and Nelson Frank (Playwright), and ServiceNow's own careers feed (RSS).
2. **Merge.** `merge_snapshot.py` writes the day's roles to `data/daily/jobs_YYYY-MM-DD.json`.
3. **Check.** `scan_sponsorship.py` looks every employer up in the register, then reads each of the day's listing pages for clearance and "no sponsorship" wording.
4. **Rebuild.** `rebuild_master.py` rebuilds `data/master.json` from every daily snapshot. The snapshots are the record, so the master can always be rebuilt.
5. **Export.** `export_site.py` writes what the site reads: `docs/data/active.json` (open roles) and `docs/data/archive/` (closed roles by month).
6. **Publish.** The pipeline commits `data/` and `docs/data/` and pushes, and GitHub Pages serves `docs/`.

A role is open until it hasn't been seen for 14 days.

## The data

`docs/data/active.json` holds every open role. It is about 60 KB and free to use. Keys are short to keep it small:

| Key | Meaning |
|---|---|
| `t` | Title, cleaned for display (casing, separators) |
| `c` | Employer, empty when the listing doesn't name one |
| `l` | Location |
| `r` | `remote` or `hybrid` when the listing says so, otherwise `null` |
| `s` | Pay as listed |
| `u` | Link to the listing |
| `src` | Where it was found |
| `role` | `architect`, `developer`, `consultant`, `manager`, `analyst`, `admin`, `other`, or `sn-adjacent` |
| `sp` | `licensed`, `unknown`, `clearance`, `agency` or `no`, as in the table above |
| `m` | The listing mentions sponsorship (only set when nothing contradicts it) |
| `fs`, `ls` | First and last day the role was seen |

The file also carries `updated` (the run date) and `register` (the date of the register copy used). `docs/data/archive/index.json` lists the monthly archive files.

`data/master.json` keeps the raw scraped values, including titles before cleanup.

## Repository layout

```
daily_cron.sh, daily_cron.py   entry point for the scheduled run
scripts/                       the pipeline, one script per step
tests/                         unit tests for the export step and the sponsorship scanner
data/                          history: daily snapshots, master.json, per-source files (not served)
docs/                          the site (index.html) and the files it reads (docs/data/)
```

## Running it yourself

You need Python 3.11 or later, and Chromium for Playwright.

```bash
pip install -r requirements.txt
python3 -m playwright install chromium
```

Download the register CSV from [gov.uk](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers) and point `SPONSOR_CSV` in `scripts/scan_sponsorship.py` at it. Then:

```bash
python3 scripts/daily_pipeline.py --no-linkedin   # skip LinkedIn
python3 scripts/export_site.py                    # rebuild only the site's files
python3 -m unittest discover -s tests             # tests
```

`daily_pipeline.py` commits and pushes at the end. To test without publishing, run the steps one by one. Setting `BRIGHT_DATA_API_KEY` adds Bright Data as an extra LinkedIn source. It's optional.

## Limits

- The register copy in use is dated 6 May 2026. Employers licensed since then show as "No register match". The site shows the date.
- Whole-name matching misses employers whose listing uses a trading name that differs from the registered one. That fails safe: a missed badge, never a false one.
- Most listings don't state a work pattern, so most rows show none.
- Indeed, Totaljobs and CV-Library block requests from the server, so they aren't sources.

## Licence

MIT. See [LICENSE](LICENSE). Not affiliated with or endorsed by ServiceNow, Inc.
