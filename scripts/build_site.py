#!/usr/bin/env python
import json, os, html, datetime
IN = "data/news_log.json"; OUT = "public/index.html"
CSS = """
body{font-family:system-ui,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;margin:24px}
h1{margin:0 0 12px 0}
.toolbar{display:flex;gap:12px;align-items:center;margin:12px 0 16px 0;flex-wrap:wrap}
input[type=search]{padding:8px 10px;border:1px solid #ccc;border-radius:8px;min-width:260px}
.badge{padding:2px 8px;border-radius:999px;font-size:12px;border:1px solid #ddd}
.badge.Major{background:#fff3cd;border-color:#ffe69c}
.badge.Security{background:#fde2e1;border-color:#f8b4b4}
.badge.Minor{background:#e7f1ff;border-color:#b6d4fe}
table{width:100%;border-collapse:collapse}
th,td{padding:10px;border-bottom:1px solid #eee;vertical-align:top}
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
def render(items, site_url):
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
<html lang="en"><meta charset="utf-8"><title>PSAI — 30‑Day AI Coding Tools Updates</title>
<style>{CSS}</style>
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
<script>{JS}</script>
</html>"""
def main():
    site = os.getenv("SITE_URL","")
    data = json.load(open(IN,"r",encoding="utf-8"))
    items = data.get("items",[])
    html_out = render(items, site)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT,"w",encoding="utf-8").write(html_out)
    print(f"Wrote {OUT} with {len(items)} items.")
if __name__ == "__main__":
    main()
