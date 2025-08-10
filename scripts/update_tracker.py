#!/usr/bin/env python
import argparse, csv, json
def latest_per_tool(items):
    by={}
    for it in items:
        k=it["tool"]
        if k not in by or it["date"]>by[k]["date"]:
            by[k]=it
    return by
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    log = json.load(open(args.log,"r",encoding="utf-8"))
    latest = latest_per_tool(log.get("items",[]))
    with open(args.tracker,"r",encoding="utf-8") as f:
        rdr = csv.DictReader(f); rows=[]; fields=rdr.fieldnames
        if "Status" not in fields: fields = fields + ["Status"]
        for r in rdr:
            it = latest.get(r["Tool"])
            if it: r["Status"] = f'{it["severity"]}: {it["headline"]} ({it["date"]})'
            rows.append(r)
    with open(args.out,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
if __name__=="__main__": main()