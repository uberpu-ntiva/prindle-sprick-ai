#!/usr/bin/env python
import csv, json, re, sys, io

IN_C = "data/candidates.json"
IN_T = "data/PSAI_FullField_Tracker.csv"
OUT_T = IN_T

# Canonical column order (we'll include any existing extras too)
REQUIRED = ["Tool","Moniker","Category","Severity","RSS Available","Feed URL","Tracking Method",
            "Repo URL","Repo Status","Stars","Contributors","Docs URL","Website URL",
            "Source Type","Discovery Method","Launch Status","Last Seen Update","Status"]

def load_csv(path):
    try:
        with open(path, encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            rows = list(rdr)
            return rows, (rdr.fieldnames or [])
    except FileNotFoundError:
        return [], []

def monikerize(name):
    return re.sub(r"[^a-z0-9]+","-", (name or "").lower()).strip("-")

def normalize_fieldnames(existing_rows, existing_fields):
    # Union of all keys found in existing rows
    all_keys = set(existing_fields or [])
    for r in existing_rows:
        all_keys.update(r.keys())
    # Ensure REQUIRED are present and ordered first
    ordered = []
    for k in REQUIRED:
        if k not in ordered:
            ordered.append(k)
    # Append any remaining keys in stable order (from existing_fields then any new)
    for k in (existing_fields or []):
        if k not in ordered:
            ordered.append(k)
    for k in sorted(all_keys):
        if k not in ordered:
            ordered.append(k)
    return ordered

def save_csv(path, rows, fieldnames):
    # Sanitize each row to contain exactly the writer's fieldnames
    clean = []
    for r in rows:
        d = {k: r.get(k, "") for k in fieldnames}
        clean.append(d)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(clean)

def main():
    existing, existing_fields = load_csv(IN_T)
    fieldnames = normalize_fieldnames(existing, existing_fields)

    # Load candidates
    try:
        with open(IN_C, "r", encoding="utf-8") as f:
            cand = json.load(f).get("items", [])
    except Exception:
        cand = []

    # Build fast lookup for dedupe
    def key_of(t, m): return (t or "").strip().lower(), (m or "").strip().lower()
    seen = { key_of(r.get("Tool",""), r.get("Moniker","")) for r in existing }

    appended = 0
    for it in cand:
        tool = (it.get("tool") or "").strip()
        if not tool:
            continue
        mon = (it.get("moniker") or monikerize(tool))
        if key_of(tool, mon) in seen:
            continue
        # create a row with all fieldnames present
        row = {k:"" for k in fieldnames}
        row.update({
            "Tool": tool,
            "Moniker": mon,
            "Category": it.get("category","Discovery"),
            "Severity": "Minor",
            "RSS Available": "✅" if it.get("feed_url") else "❌",
            "Feed URL": it.get("feed_url",""),
            "Tracking Method": "RSS" if it.get("feed_url") else ("GitHub Releases" if (it.get("repo_url","").startswith("https://github.com/")) else "HTML/Blog"),
            "Repo URL": it.get("repo_url",""),
            "Repo Status": "Active" if it.get("repo_url") else "",
            "Website URL": it.get("website_url",""),
            "Source Type": it.get("source_type",""),
            "Discovery Method": "Auto-Discovery",
            "Launch Status": "Unknown",
        })
        existing.append(row)
        seen.add(key_of(tool, mon))
        appended += 1

    # Ensure final fieldnames include REQUIRED at least
    for k in REQUIRED:
        if k not in fieldnames:
            fieldnames.append(k)

    save_csv(OUT_T, existing, fieldnames)
    print(f"Appended {appended} new tools into {OUT_T}; columns: {len(fieldnames)}")

if __name__ == "__main__":
    main()
