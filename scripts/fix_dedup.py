#!/usr/bin/env python3
"""Fix dedup — Hunt UK jobs all have same URL, use title+company as key"""
import json, os
OUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobs.json")

with open(OUT) as f:
    data = json.load(f)

hunt_new = [
    {"title":"Solution Architect ServiceNow","company":"Kinly","location":"Sunbury/London/Livingston","salary_display":"Not listed","date_posted":"2026-05-01","url":"https://huntukvisasponsors.com/jobs?q=servicenow","fallback_url":"https://www.kinly.com/careers","source":"Hunt UK","source_type":"direct","role_type":"architect","remote":"hybrid","employment":"permanent","sc_clearance":False,"grad_scheme":False,"link_status":"live","visa_sponsorship":"verified","description":"Global AV/UC solutions. Hybrid, 1 day onsite. Excellent salary + bonus. Kinly holds A-rated sponsor licence."},
    {"title":"ServiceNow Engineer","company":"Freshfields","location":"Manchester","salary_display":"Not listed","date_posted":"2026-05-01","url":"https://huntukvisasponsors.com/jobs?q=servicenow","fallback_url":"https://www.freshfields.com/en-gb/careers/","source":"Hunt UK","source_type":"direct","role_type":"developer","remote":"hybrid","employment":"permanent","sc_clearance":False,"grad_scheme":False,"link_status":"live","visa_sponsorship":"verified","description":"Global law firm. Mature business-critical ServiceNow platform. Collaborative, people-first environment."},
    {"title":"ServiceNow Technical Lead (Insurance/FSO)","company":"DXC Technology","location":"UK — Hybrid","salary_display":"Not listed","date_posted":"2026-05-01","url":"https://huntukvisasponsors.com/jobs?q=servicenow","fallback_url":"https://careers.dxc.com/","source":"Hunt UK","source_type":"direct","role_type":"developer","remote":"hybrid","employment":"permanent","sc_clearance":False,"grad_scheme":False,"link_status":"live","visa_sponsorship":"verified","description":"Insurance digital transformation on ServiceNow FSO. Global IT services. DXC holds A-rated sponsor licence."},
    {"title":"ServiceNow Product Manager (Banking)","company":"Barclays via SThree","location":"Knutsford/Manchester","salary_display":"£70,000-£100,000","salary_min":70000,"salary_max":100000,"date_posted":"2026-05-01","url":"https://huntukvisasponsors.com/jobs?q=servicenow","source":"Hunt UK","source_type":"agency","role_type":"manager","remote":"hybrid","employment":"permanent","sc_clearance":False,"grad_scheme":False,"link_status":"live","visa_sponsorship":"agency_unknown","description":"ServiceNow Centre of Excellence. 2 days/week Knutsford or Manchester. SThree agency — Barclays A-rated sponsor."},
    {"title":"CMDB Specialist (ServiceNow)","company":"Harvey Nash (agency)","location":"UK — Remote","salary_display":"Not listed","date_posted":"2026-05-01","url":"https://huntukvisasponsors.com/jobs?q=servicenow","source":"Hunt UK","source_type":"agency","role_type":"consultant","remote":"remote","employment":"permanent","sc_clearance":False,"grad_scheme":False,"link_status":"live","visa_sponsorship":"agency_unknown","description":"15M+ CIs, 300K employees. Global manufacturer. Governance + hands-on CMDB. Harvey Nash agency."},
    {"title":"ServiceNow Functional Analyst","company":"Global IT Services (agency)","location":"London","salary_display":"Competitive day rate","date_posted":"2026-05-01","url":"https://www.computerjobs.com/gb/en/JobListing.aspx?shid=E3BE4C44A9FC068922CC&ovrpp=jl","source":"ComputerJobs","source_type":"agency","role_type":"analyst","remote":"hybrid","employment":"contract","sc_clearance":False,"grad_scheme":False,"link_status":"live","visa_sponsorship":"agency_unknown","description":"6+ month contract. London 3 days/week. ITIL, ServiceNow data model. Business/functional analysis."},
    {"title":"ServiceNow Technical Consultant (DV Cleared)","company":"Agency — DV required","location":"UK — Remote","salary_display":"£45,000-£60,000","salary_min":45000,"salary_max":60000,"date_posted":"2026-05-01","url":"https://www.computerjobs.com/gb/en/JobListing.aspx?shid=E3BE4C44A9FC068922CC&ovrpp=jl","source":"ComputerJobs","source_type":"agency","role_type":"consultant","remote":"remote","employment":"permanent","sc_clearance":True,"grad_scheme":False,"link_status":"live","visa_sponsorship":"sc_blocked","description":"Must hold active DV clearance — blocks international candidates. 2-3 yrs ServiceNow. 10% bonus."},
]

# Dedup by title+company (not URL, since Hunt UK jobs share the same search URL)
keys = set()
for j in data['jobs']:
    keys.add((j['title'].lower().strip(), j['company'].lower().strip()))

added = 0
for nj in hunt_new:
    k = (nj['title'].lower().strip(), nj['company'].lower().strip())
    if k not in keys:
        data['jobs'].append(nj)
        keys.add(k)
        added += 1

data['updated'] = "2026-05-06"
data['total'] = len(data['jobs'])
data['verified'] = sum(1 for j in data['jobs'] if j['visa_sponsorship'] == 'verified')
data['sc_blocked'] = sum(1 for j in data['jobs'] if j['visa_sponsorship'] == 'sc_blocked')
data['live_links'] = sum(1 for j in data['jobs'] if j['link_status'] == 'live')

srcs = {}
for j in data['jobs']: srcs[j.get('source','?')] = srcs.get(j.get('source','?'), 0) + 1
data['sources'] = srcs

with open(OUT, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"SAVED {data['total']} jobs (+{added} new) from {len(srcs)} sources")
print(f"  Verified: {data['verified']} | SC blocked: {data['sc_blocked']} | Agency: {sum(1 for j in data['jobs'] if j['visa_sponsorship']=='agency_unknown')}")
for j in data['jobs']:
    print(f"  [{j['visa_sponsorship']}] {j['title'][:55]} | {j['company'][:30]} | {j.get('source','?')}")
