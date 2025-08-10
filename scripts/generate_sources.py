#!/usr/bin/env python
import csv, re, yaml
from urllib.parse import urlparse
IN = "data/PSAI_FullField_Tracker.csv"; OUT = "data/sources.yaml"
def gh_repo(url):
    if not url or url.strip() in ("N/A",""): return None
    u = url if url.startswith(("http://","https://")) else "https://" + url
    p = urlparse(u)
    if p.netloc.lower() != "github.com": return None
    parts = [x for x in p.path.strip('/').split('/') if x]
    return f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else None
def first_url(*vals):
    for v in vals:
        if v and v.strip() and v.strip() != "N/A":
            return v if v.startswith(("http://","https://")) else "https://" + v.strip()
    return None
rows = list(csv.DictReader(open(IN, encoding="utf-8")))
items = []
for r in rows:
    tool = (r.get("Tool") or "").strip()
    if not tool: continue
    moniker = (r.get("Moniker") or re.sub(r'[^a-z0-9]+','-', tool.lower())).strip()
    category = (r.get("Category") or "Updates").strip()
    feed = (r.get("Feed URL") or "").strip()
    repo = gh_repo(r.get("Repo URL") or "")
    docs = (r.get("Docs URL") or "").strip()
    site = (r.get("Website URL") or "").strip()
    entry = {"tool": tool, "moniker": moniker, "category": category, "sources": []}
    if feed and feed != "N/A":
        entry["sources"].append({"type":"rss","url": feed})
    elif repo:
        entry["sources"].append({"type":"github_releases","repo": repo})
    if not entry["sources"]:
        url = first_url(docs, site)
        if url:
            entry["sources"].append({"type":"html","url": url,"item_selector":"article","title_selector":"h2, h3","date_selector":"time, .date","link_selector":"a"})
    if entry["sources"]: items.append(entry)
yaml.safe_dump({"items": items}, open(OUT,"w",encoding="utf-8"), sort_keys=False, allow_unicode=True)
print(f"Wrote {OUT} with {len(items)} entries from {IN}")