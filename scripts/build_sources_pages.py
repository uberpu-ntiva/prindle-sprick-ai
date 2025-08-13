#!/usr/bin/env python3
# PSAI sources page generator (filtered, cards + table, tooltips, index link inject)

import csv, os, re, html, json
from datetime import datetime, timezone

CSV_IN   = os.getenv("PSAI_TOOLS_CSV", "data/tools.csv")
LOG_IN   = os.getenv("PSAI_LOG_PATH", "data/news_log.json")
OUT_LIST = os.getenv("PSAI_OUT_LIST", "public/sources.html")
OUT_TAB  = os.getenv("PSAI_OUT_TABLE", "public/sources_table.html")
OUT_INDEX = os.getenv("PSAI_INDEX", "public/index.html")
NEWS_FEED_PATH = os.getenv("PSAI_NEWS_FEED", "public/news_feed.html") # Formerly INDEX

DEFAULT_INCLUDE = r"(agent|agentic|orchestr|mcp|ide|editor|review|code\s*assistant)"
DEFAULT_EXCLUDE = r"^(product\s*hunt|reddit|hacker\s*news|hn\s*—|hn\s*show|latentspace|ben['’]s\s*bites|npm|pypi|docker\s*hub)\b"

INCLUDE_RX = re.compile(os.getenv("PSAI_INCLUDE_REGEX", DEFAULT_INCLUDE), re.I)
EXCLUDE_RX = re.compile(os.getenv("PSAI_EXCLUDE_REGEX", DEFAULT_EXCLUDE), re.I)
MIN_STARS  = int(os.getenv("PSAI_MIN_STARS", "0"))

ICON_CSS = """
:root { --fg:#0f172a; --muted:#64748b; --chip:#e2e8f0; }
*{box-sizing:border-box} body{font-family:ui-sans-serif,system-ui; color:var(--fg); margin:0; background:#fff}
main{max-width:1200px;margin:40px auto;padding:0 16px}
h1{font-size:28px;margin:0 0 8px}
.sub{color:var(--muted);margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{border:1px solid #e5e7eb;border-radius:16px;padding:16px;background:#fff}
.card h2{font-size:18px;margin:0 0 6px;line-height:1.2}
.meta{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.chip{background:var(--chip);padding:2px 8px;border-radius:999px;font-size:12px}
.icons{display:flex;gap:10px;margin-top:8px}
.icon{width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid #e5e7eb;background:#f8fafc}
.icon[aria-disabled="true"]{opacity:.35}
.icon svg{width:14px;height:14px}
.icon:hover{border-color:#cbd5e1}
a.icon{color:inherit;text-decoration:none}
a.icon:hover{background:#eef2ff;border-color:#c7d2fe}
.tooltip{position:relative}
.tooltip:hover::after{
  content:attr(title);
  position:absolute;left:50%;transform:translateX(-50%);bottom:135%;
  background:#111827;color:#fff;padding:6px 8px;border-radius:6px;font-size:11px;white-space:nowrap;
  box-shadow:0 6px 20px rgba(0,0,0,.18);
}
.tablewrap{overflow:auto;border:1px solid #e5e7eb;border-radius:12px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:10px 12px;border-bottom:1px solid #e5e7eb}
th{text-align:left;background:#f8fafc;font-weight:600}
.badge{padding:2px 6px;border-radius:6px;background:#eef2ff;border:1px solid #c7d2fe;font-size:12px}
.sev-Major{background:#fff7ed;border-color:#fed7aa}
.sev-Security{background:#fee2e2;border-color:#fecaca}
.sev-Minor{background:#f0fdf4;border-color:#bbf7d0}
.topnav{background:#0b1220;color:#e5e7eb;padding:10px 16px;display:flex;gap:14px;align-items:center}
.topnav a{color:#93c5fd;text-decoration:none}
.topnav a:hover{text-decoration:underline}
.note{margin:16px 0 24px;color:var(--muted);font-size:13px}
.updates-list,.tools-list{list-style:none;padding:0;margin:10px 0 0;font-size:14px}
.updates-list li,.tools-list li{margin-bottom:8px}
.updates-list li strong{font-weight:500}
"""

def svg(name):
    if name=="site":
        return '<svg viewBox="0 0 24 24" fill="none"><path d="M4 12h16M4 12c0-4 3.5-8 8-8s8 4 8 8-3.5 8-8 8-8-4-8-8Zm0 0h16" stroke="currentColor" stroke-width="1.6"/></svg>'
    if name=="docs":
        return '<svg viewBox="0 0 24 24" fill="none"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5" stroke="currentColor" stroke-width="1.6" fill="none"/></svg>'
    if name=="repo":
        return '<svg viewBox="0 0 24 24" fill="none"><path d="M9 19c-4 1.5-4-2.5-6-3m12 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 18 2.77A5.07 5.07 0 0 0 17.91 1S17.27.65 15 2.48a13.38 13.38 0 0 0-6 0C6.73.65 6.09 1 6.09 1A5.07 5.07 0 0 0 6 2.77a5.44 5.44 0 0 0-1.5 3.77c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 10 17.13V21" stroke="currentColor" stroke-width="1.6"/></svg>'
    if name=="rss":
        return '<svg viewBox="0 0 24 24" fill="none"><path d="M4 11a9 9 0 0 1 9 9M4 5a15 15 0 0 1 15 15M6 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" stroke="currentColor" stroke-width="1.6"/></svg>'
    return ''

def norm_url(u):
    if not u: return ""
    u = u.strip()
    if not u or u.upper()=="N/A": return ""
    if re.match(r'^https?://', u): return u
    return "https://" + u

def icon_link(url, label):
    u = norm_url(url)
    if not u:
        return f'<span class="icon tooltip" aria-disabled="true" title="No {html.escape(label)}">{svg(label)}</span>'
    return f'<a class="icon tooltip" href="{html.escape(u)}" target="_blank" rel="noopener" title="{html.escape(u)}" aria-label="{html.escape(label)}">{svg(label)}</a>'

def sev_badge(sev):
    sev = (sev or "Minor").strip().title()
    cls = "sev-Minor"
    if sev=="Major": cls="sev-Major"
    if sev=="Security": cls="sev-Security"
    return f'<span class="badge {cls}">{html.escape(sev)}</span>'

def looks_discovery_stub(tool, moniker, site):
    t = (tool or "").lower(); m = (moniker or "").lower(); s = (site or "").lower()
    if EXCLUDE_RX.search(t) or EXCLUDE_RX.search(m):
        return True
    if "producthunt" in s or "reddit.com" in s or "news.ycombinator.com" in s:
        return True
    return False

def include_row(r):
    tool = r.get("Tool","")
    mon  = r.get("Moniker","")
    cat  = r.get("Category","") or r.get("Source Type","")
    site = r.get("Website URL","")
    # star filter
    try:
        stars = int((r.get("Stars") or "0").replace(",",""))
    except Exception:
        stars = 0
    if MIN_STARS > 0 and stars < MIN_STARS:
        return False
    if looks_discovery_stub(tool, mon, site):
        return False
    hay = " ".join([tool, mon, cat])
    return bool(INCLUDE_RX.search(hay))

HTML_HEAD = """
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>PSAI</title>
<style>{css}</style>
</head><body>
<div class="topnav"><strong>PSAI</strong> · <a href="./">Home</a> · <a href="news_feed.html">News Feed</a> · <a href="sources.html">Sources</a> · <a href="sources_table.html">Table</a></div>
<main>
"""
HTML_FOOT = """
</main>
</body></html>
"""

def build_list(cards):
    return HTML_HEAD.format(css=ICON_CSS).replace("<title>PSAI</title>", "<title>PSAI Sources</title>") + """
  <h1>AI Coding Tools — Sources</h1>
  <div class="sub">Filtered to core AI dev tools (agents, IDEs, reviewers, orchestration, MCP). Hover icons to see real URLs.</div>
  <div class="grid">
    {cards}
  </div>
""".format(cards=cards) + HTML_FOOT

def build_table(rows_html):
    return HTML_HEAD.format(css=ICON_CSS).replace("<title>PSAI</title>", "<title>PSAI Sources (Table)</title>") + """
  <h1>AI Coding Tools — Sources (Table)</h1>
  <div class="sub">Use env vars to tune filters: PSAI_INCLUDE_REGEX / PSAI_EXCLUDE_REGEX / PSAI_MIN_STARS.</div>
  <div class="tablewrap">
    <table>
      <thead>
        <tr>
          <th>Tool</th><th>Moniker</th><th>Category</th><th>Severity</th><th>Status</th><th>Links</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
""".format(rows=rows_html) + HTML_FOOT

def build_dashboard_page(recent_tools, todays_updates):
    run_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    recent_html = ""
    if not recent_tools:
        recent_html = "<li>No tools found.</li>"
    else:
        for r in reversed(recent_tools):
            tool = html.escape((r.get("Tool") or "").strip())
            cat = html.escape((r.get("Category") or r.get("Source Type") or "").strip())
            site_url = norm_url(r.get("Website URL", ""))
            link = f'<a href="{site_url}" target="_blank" rel="noopener">{tool}</a>' if site_url else tool
            recent_html += f'<li>{link} <span class="chip">{cat}</span></li>'
    updates_html = ""
    if not todays_updates:
        updates_html = "<li>No updates logged today.</li>"
    else:
        for item in todays_updates:
            tool = html.escape(item.get("tool", ""))
            headline = html.escape(item.get("headline", ""))
            link_url = item.get("link", "")
            link = f'<a href="{link_url}" target="_blank" rel="noopener">{headline}</a>' if link_url else headline
            updates_html += f'<li><strong>{tool}:</strong> {link} {sev_badge(item.get("severity"))}</li>'
    return HTML_HEAD.format(css=ICON_CSS).replace("<title>PSAI</title>", "<title>PSAI Dashboard</title>") + f"""
  <h1>PSAI Dashboard</h1>
  <div class="sub">Last updated: {run_time}</div>
  <div class="grid" style="grid-template-columns:1fr 1fr;max-width:1200px;">
    <section class="card">
      <h2>Today's Updates</h2>
      <ul class="updates-list">{updates_html}</ul>
    </section>
    <section class="card">
      <h2>Recently Added Tools</h2>
      <ul class="tools-list">{recent_html}</ul>
    </section>
  </div>
""" + HTML_FOOT

def main():
    if not os.path.exists(CSV_IN):
        print(f"ERR: tracker not found at {CSV_IN}"); return
    with open(CSV_IN, encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    approved_rows = [r for r in all_rows if r.get('Status', '').lower() != 'pending_review']
    rows = [r for r in approved_rows if include_row(r)]

    # --- Dashboard page ---
    todays_updates = []
    if os.path.exists(LOG_IN):
        log = json.load(open(LOG_IN, "r", encoding="utf-8"))
        today = datetime.now(timezone.utc).date().isoformat()
        todays_updates = [item for item in log.get("items", []) if item.get("date", "") >= today]
    recent_tools = approved_rows[-10:]
    print("--- Building dashboard page ---")
    dashboard_html = build_dashboard_page(recent_tools, todays_updates)
    print(f"Dashboard HTML generated ({len(dashboard_html)} bytes).")
    os.makedirs(os.path.dirname(OUT_INDEX) or ".", exist_ok=True)
    print(f"Attempting to write dashboard to {OUT_INDEX}...")
    with open(OUT_INDEX, "w", encoding="utf-8") as f:
        f.write(dashboard_html)
    print(f"Successfully wrote dashboard to {OUT_INDEX}.")

    # --- Sources pages (cards and table) ---
    card_html, row_html = [], []
    for r in rows:
        tool = (r.get("Tool") or "").strip()
        if not tool: continue
        mon  = (r.get("Moniker") or "").strip()
        cat  = (r.get("Category") or r.get("Source Type") or "Uncategorized").strip()
        sev  = (r.get("Severity") or "Minor").strip()
        stat = (r.get("Status") or r.get("Updates") or "—").strip()
        site = icon_link(r.get("Website URL",""), "site")
        docs = icon_link(r.get("Docs URL",""), "docs")
        repo = icon_link(r.get("Repo URL",""), "repo")
        feed = icon_link(r.get("Feed URL",""), "rss")
        card_html.append(f"""
        <section class="card">
          <h2>{html.escape(tool)}</h2>
          <div class="meta">
            <span class="chip">{html.escape(mon or '')}</span>
            <span class="chip">{html.escape(cat)}</span>
            {sev_badge(sev)}
          </div>
          <div class="icons">{site}{docs}{repo}{feed}</div>
          <p class="status">{html.escape(stat)}</p>
        </section>""")
        row_html.append(f"""
        <tr>
          <td>{html.escape(tool)}</td>
          <td><code>{html.escape(mon)}</code></td>
          <td>{html.escape(cat)}</td>
          <td>{sev_badge(sev)}</td>
          <td>{html.escape(stat)}</td>
          <td style="white-space:nowrap">{site}{docs}{repo}{feed}</td>
        </tr>""")
    os.makedirs(os.path.dirname(OUT_LIST) or ".", exist_ok=True)
    open(OUT_LIST, "w", encoding="utf-8").write(build_list("".join(card_html)))
    open(OUT_TAB,  "w", encoding="utf-8").write(build_table("".join(row_html)))
    print(f"Built {OUT_LIST} and {OUT_TAB} with {len(rows)} filtered tools.")

    # --- Inject/update navigation links into the news feed page ---
    if os.path.exists(NEWS_FEED_PATH):
        txt = open(NEWS_FEED_PATH, "r", encoding="utf-8").read()
        new_nav = '<div class="topnav"><strong>PSAI</strong> · <a href="./">Home</a> · <a href="news_feed.html">News Feed</a> · <a href="sources.html">Sources</a> · <a href="sources_table.html">Table</a></div>'
        if '<div class="topnav">' in txt:
            txt = re.sub(r'<div class="topnav">.*</div>', new_nav, txt, count=1, flags=re.DOTALL)
        elif '<body>' in txt:
            txt = txt.replace("<body>", f"<body>\n{new_nav}", 1)
        open(NEWS_FEED_PATH, "w", encoding="utf-8").write(txt)

if __name__ == "__main__":
    main()
