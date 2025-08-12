#!/usr/bin/env python3
# PSAI: Generate public/feed.json (JSON Feed 1.1) + public/rss.xml (RSS 2.0) from data/news_log.json
# Also inject a Sources link into public/index.html (idempotent).

import os, json, re

LOG_PATH = os.getenv("PSAI_LOG_PATH", "data/news_log.json")
OUT_JSON = os.getenv("PSAI_FEED_JSON", "public/feed.json")
OUT_RSS  = os.getenv("PSAI_FEED_RSS",  "public/rss.xml")
INDEX    = os.getenv("PSAI_INDEX",     "public/index.html")
SITE_URL = os.getenv("PSAI_SITE_URL",  "")

def ensure_dir(path):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)

def load_items():
    if not os.path.exists(LOG_PATH):
        raise SystemExit(f"news_log not found at {LOG_PATH}")
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])
    items.sort(key=lambda x: x.get("date",""), reverse=True)
    return items

def to_json_feed(items):
    site = SITE_URL.rstrip("/")
    jf = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "PSAI — 30-Day AI Coding Tools Updates",
        "home_page_url": f"{site}/" if site else None,
        "feed_url": f"{site}/feed.json" if site else None,
        "items": []
    }
    for it in items:
        pid = f"{it.get('date','')}-{it.get('moniker','')}-{(it.get('headline','') or '')[:30]}"
        jf["items"].append({
            "id": pid,
            "url": it.get("link") or (f"{site}/" if site else None),
            "title": f"[{it.get('tool','')}] {it.get('headline','')}",
            "content_text": f"{it.get('severity','Minor')} — {it.get('impact','')}",
            "date_published": f"{it.get('date','')}T09:20:00-04:00",
            "tags": [t for t in [it.get("category","Updates"), it.get("severity","Minor")] if t]
        })
    return jf

def esc(s):
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def to_rss(items):
    site = SITE_URL.rstrip("/")
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        '<channel>',
        '<title>PSAI — 30-Day AI Coding Tools Updates</title>',
        f'<link>{esc(site or "https://example.invalid")}/</link>',
        '<description>Rolling feed of changes to tracked AI coding tools</description>'
    ]
    for it in items:
        title = f"[{it.get('tool','')}] {it.get('headline','')}"
        link  = it.get("link") or (f"{site}/" if site else "")
        pub   = it.get("date","")
        desc  = f"{it.get('severity','Minor')} — {it.get('impact','')}"
        out += [
            '<item>',
            f'<title>{esc(title)}</title>',
            f'<link>{esc(link)}</link>' if link else '',
            f'<pubDate>{esc(pub)}</pubDate>' if pub else '',
            f'<description>{esc(desc)}</description>',
            '</item>'
        ]
    out += ['</channel></rss>']
    return "\n".join(x for x in out if x)

def inject_sources_link():
    if not os.path.exists(INDEX): return
    txt = open(INDEX, "r", encoding="utf-8").read()
    if "sources.html" in txt: return
    if "<nav" in txt:
        txt = re.sub(r"(<nav[^>]*>)", r'\1\n  <a href="sources.html">Sources</a> · <a href="sources_table.html">Sources (Table)</a>', txt, count=1)
    else:
        txt = txt.replace("<body>", '<body>\n<div class="topnav"><a href="sources.html">Sources</a> · <a href="sources_table.html">Sources (Table)</a></div>')
    open(INDEX, "w", encoding="utf-8").write(txt)

if __name__ == "__main__":
    items = load_items()
    ensure_dir(OUT_JSON); ensure_dir(OUT_RSS)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(to_json_feed(items), f, ensure_ascii=False, indent=2)
    with open(OUT_RSS, "w", encoding="utf-8") as f:
        f.write(to_rss(items))
    inject_sources_link()
    print(f"Wrote {OUT_JSON} and {OUT_RSS}.")
