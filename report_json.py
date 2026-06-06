import json, glob, os
master = 'docs/data/master.json'
latest = sorted(glob.glob('docs/data/daily/jobs_*.json'))[-1]

with open(master) as f:
    m = json.load(f)
with open(latest) as f:
    d = json.load(f)

latest_name = os.path.basename(latest)
latest_count = len(d.get('jobs', [])) if isinstance(d, dict) else len(d)
active = m.get('total_active')
licenced = m.get('licenced_sponsors')
sc = sum(1 for j in m.get('jobs', []) if j.get('visa_sponsorship') == 'sc_blocked')

sources = {}
for j in m.get('jobs', []):
    s = j.get('source') or j.get('source_name') or 'unknown'
    sources[s] = sources.get(s, 0) + 1

source_lines = [f"{k}: {v}" for k, v in sorted(sources.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)[:20]]

print(f"LATEST_SNAPSHOT: {latest_name} ({latest_count} jobs)")
print(f"ACTIVE: {active}")
print(f"LICENCED: {licenced}")
print(f"SC_BLOCKED: {sc}")
print("SOURCES:")
for line in source_lines:
    print(line)
