#!/usr/bin/env python3
# PSAI: Generate public/feed.json (JSON Feed 1.1) + public/rss.xml (RSS 2.0) from data/news_log.json
# and generate public/news_feed.html from the same data.

import os, json, re, html, datetime

LOG_PATH = os.getenv("PSAI_LOG_PATH", "data/news_log.json")
OUT_JSON = os.getenv("PSAI_FEED_JSON", "public/feed.json")
OUT_RSS  = os.getenv("PSAI_FEED_RSS",  "public/rss.xml")
OUT_HTML = os.getenv("PSAI_INDEX",     "public/news_feed.html")
SITE_URL = os.getenv("PSAI_SITE_URL",  "")

CSS = """
body{font-family:system-ui,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;margin:0}
.topnav{background:#0b1220;color:#e5e7eb;padding:10px 16px;display:flex;gap:14px;align-items:center}
.topnav a{color:#93c5fd;text-decoration:none}
.topnav a:hover{text-decoration:underline}
main{margin:24px}
h1{margin:0 0 12px 0}
.toolbar{display:flex;gap:12px;align-items:center;margin:12px 0 16px 0;flex-wrap:wrap}
input[type=search]{padding:8px 10px;border:1px solid #ccc;border-radius:8px;min-width:260px}
.badge{padding:2px 8px;border-radius:999px;font-size:12px;border:1px solid #ddd}
.badge.Major{background:#fff3cd;border-color:#ffe69c}
.badge.Security{background:#fde2e1;border-color:#f8b4b4}
.badge.Minor{background:#e7f1ff;border-color:#b6d4fe}
table{width:100%;border-collapse:collapse}
th,td{padding:10px;border-bottom:1px solid #eee;vertical-align:top;text-align:left}
th{position:sticky;top:0;background:#fff}
.row-hide{display:none}
small.mono{font-family:ui-monospace,Menlo,Consolas,monospace;color:#666}
footer{margin-top:24px;color:#777;font-size:12px}
"""
JS = """
const q = document.getElementById('q');
const chkMajor = document.getElementById('f-major');
const chkSecurity = document.getElementById('f-security');
const chkMinor = document.getElementById('f-minor');
function matchRow(tr){
  const text = tr.getAttribute('data-text');
  const sev = tr.getAttribute('data-sev');
  const qq = q.value.trim().toLowerCase();
  const passQ = !qq || text.includes(qq);
  const passSev = (chkMajor.checked && sev==='Major') || (chkSecurity.checked && sev==='Security') || (chkMinor.checked && sev==='Minor');
  return passQ && passSev;
}
function apply(){
  document.querySelectorAll('tbody tr').forEach(tr=>{
    tr.classList.toggle('row-hide', !matchRow(tr));
  });
  document.getElementById('count').textContent = document.querySelectorAll('tbody tr:not(.row-hide)').length;
}
[q, chkMajor, chkSecurity, chkMinor].forEach(el=>el.addEventListener('input', apply));
apply();
"""

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

def render_html(items, site_url):
    rows_html = []
    for it in items:
        sev = html.escape(it.get("severity","Minor"))
        badge = f'<span class="badge {sev}">{sev}</span>'
        date = html.escape(it.get("date",""))
        tool = html.escape(it.get("tool",""))
        head = html.escape(it.get("headline","Update"))
        link = it.get("link") or site_url or "#"
        link_html = f'<a href="{html.escape(link)}" target="_blank" rel="noopener">{head}</a>'
        impact = html.escape(it.get("impact",""))
        moniker = html.escape(it.get("moniker",""))
        data_text = " ".join([sev,date,tool,head,impact,moniker]).lower()
        rows_html.append(f'<tr data-sev="{sev}" data-text="{html.escape(data_text)}">'
                         f'<td>{date}</td><td>{tool}<br><small class="mono">{moniker}</small></td>'
                         f'<td>{link_html}</td><td>{badge}</td><td>{impact}</td></tr>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>PSAI — 30‑Day AI Coding Tools Updates</title>
<style>{CSS}</style>
</head><body>
<div class="topnav"><strong>PSAI</strong> · <a href="./">Home</a> · <a href="news_feed.html">News Feed</a> · <a href="sources.html">Sources</a> · <a href="sources_table.html">Table</a></div>
<main>
<h1>PSAI — 30‑Day AI Coding Tools Updates</h1>
<div class="toolbar">
  <input id="q" type="search" placeholder="Search headline / tool / moniker…" />
  <label><input id="f-major" type="checkbox" checked> Major</label>
  <label><input id="f-security" type="checkbox" checked> Security</label>
  <label><input id="f-minor" type="checkbox" checked> Minor</label>
  <span><strong id="count">{len(items)}</strong> items (last 30 days)</span>
</div>
<table><thead><tr><th>Date</th><th>Tool</th><th>Headline</th><th>Severity</th><th>Impact</th></tr></thead>
<tbody>
{''.join(rows_html)}
</tbody></table>
<footer>Built {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC • <a href="feed.json">JSON</a> • <a href="rss.xml">RSS</a></footer>
</main>
<script>{JS}</script>
</body></html>"""

if __name__ == "__main__":
    items = load_items()
    ensure_dir(OUT_JSON); ensure_dir(OUT_RSS); ensure_dir(OUT_HTML)

    # Write JSON Feed
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(to_json_feed(items), f, ensure_ascii=False, indent=2)

    # Write RSS Feed
    with open(OUT_RSS, "w", encoding="utf-8") as f:
        f.write(to_rss(items))

    # Write HTML page
    html_out = render_html(items, SITE_URL)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"Wrote {OUT_JSON}, {OUT_RSS}, and {OUT_HTML}.")
