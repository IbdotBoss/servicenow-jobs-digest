---
layout: default
title: ServiceNow Jobs Digest
---

# ServiceNow Jobs Digest 🇬🇧

Daily curated ServiceNow jobs in the United Kingdom with visa sponsorship filtering.

## Latest Digest

{% assign digests = site.pages | where_exp: "page", "page.path contains '.md' and page.path contains '202'" | sort: "path" | reverse %}

{% for page in digests limit: 5 %}
{% if page.path != "index.md" and page.path != "all-jobs.md" and page.path contains "docs/" %}
- [{{ page.path | replace: 'docs/', '' | replace: '.md', '' }}]({{ page.path | replace: 'docs/', '' }})
{% endif %}
{% endfor %}

[View all daily digests...](all-jobs.html)

## Master Archive

All jobs ever found, sorted by date (newest → oldest):

[**📋 View Master Job Table**](all-jobs.html)

## About

This digest is automatically updated daily at 08:00 UK time via a cron job running on an Oracle Ampere VPS. Jobs are sourced from:

- LinkedIn
- Indeed
- CWJobs
- Technojobs
- Prospects
- Gradcracker
- Milkround
- CareerJet
- Adzuna

**Sponsorship (SC):** ✓ = Confirmed sponsorship / ✗ = No sponsorship mentioned

---

*Last updated: {{ site.time | date: "%Y-%m-%d %H:%M %Z" }}*
