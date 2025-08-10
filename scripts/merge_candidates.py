#!/usr/bin/env python
import csv, json, re
IN_C = "data/candidates.json"; IN_T = "data/PSAI_FullField_Tracker.csv"; OUT_T = IN_T
def load_csv(path):
    try:
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []
def save_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames); w.writeheader(); w.writerows(rows)
def monikerize(name): return re.sub(r"[^a-z0-9]+","-", name.lower()).strip("-")
def main():
    existing = load_csv(IN_T); seen = { (r.get("Tool","").strip().lower(), r.get("Moniker","").strip().lower()) for r in existing }
    fields = existing[0].keys() if existing else ["Tool","Moniker","Category","Severity","RSS Available","Feed URL","Tracking Method","Repo URL","Repo Status","Stars","Contributors","Docs URL","Website URL","Source Type","Discovery Method","Launch Status","Last Seen Update","Status"]
    cand = json.load(open(IN_C,"r",encoding="utf-8")).get("items",[]); appended = 0
    for it in cand:
        tool = (it.get("tool") or "").strip(); mon = (it.get("moniker") or monikerize(tool))
        key = (tool.lower(), mon.lower())
        if not tool or key in seen: continue
        row = {k:"" for k in fields}
        row["Tool"]=tool; row["Moniker"]=mon; row["Category"]= it.get("category","Discovery"); row["Severity"]="Minor"
        row["RSS Available"]="✅" if it.get("feed_url") else "❌"; row["Feed URL"]= it.get("feed_url","")
        row["Tracking Method"]= "RSS" if it.get("feed_url") else ("GitHub Releases" if (it.get("repo_url","").startswith("https://github.com/")) else "HTML/Blog")
        row["Repo URL"]= it.get("repo_url",""); row["Repo Status"]= "Active"; row["Website URL"]= it.get("website_url","")
        row["Source Type"]= it.get("source_type",""); row["Discovery Method"]= "Auto-Discovery"; row["Launch Status"]= "Unknown"
        existing.append(row); seen.add(key); appended += 1
    save_csv(OUT_T, existing, fields); print(f"Appended {appended} new tools into {OUT_T}")
if __name__ == "__main__": main()
