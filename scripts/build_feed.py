#!/usr/bin/env python
import argparse, json, email.utils, datetime
from feedgen.feed import FeedGenerator
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--log", required=True); ap.add_argument("--site", required=True); ap.add_argument("--json", required=True); ap.add_argument("--rss", required=True); args = ap.parse_args()
    data = json.load(open(args.log,"r",encoding="utf-8")); items = data.get("items",[])
    jf = {"version": "https://jsonfeed.org/version/1.1","title": "PSAI — 30-Day AI Coding Tools Updates","home_page_url": args.site + "/","feed_url": args.site + "/feed.json","items": []}
    for it in items:
        jf["items"].append({"id": f'{it["date"]}-{it["moniker"]}-{it["headline"][:30]}',"url": it.get("link") or args.site + "/","title": f'[{it["tool"]}] {it["headline"]}',"content_text": f'{it["severity"]} — {it["impact"]}'.strip(),"date_published": it["date"] + "T09:20:00-04:00","tags": [it.get("category","Updates"), it.get("severity","Minor")]})
    open(args.json,"w",encoding="utf-8").write(json.dumps(jf,ensure_ascii=False,indent=2))
    from datetime import datetime as dt
    fg = FeedGenerator(); fg.title("PSAI — 30-Day AI Coding Tools Updates"); fg.link(href=args.site+"/", rel='alternate'); fg.link(href=args.site+"/rss.xml", rel='self'); fg.description("Rolling feed of changes to tracked AI coding tools")
    for it in items:
        fe = fg.add_entry(); fe.title(f'[{it["tool"]}] {it["headline"]}'); fe.link(href=it.get("link") or args.site + "/"); fe.pubDate(email.utils.format_datetime(dt.strptime(it["date"], "%Y-%m-%d"))); fe.description(f'{it["severity"]} — {it["impact"]}')
    fg.rss_file(args.rss)
if __name__=="__main__": main()