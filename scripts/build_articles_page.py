#!/usr/bin/env python
import csv, os, html
from datetime import datetime, timezone

# I/O Configuration
IN_CSV   = os.getenv("PSAI_ARTICLES_CSV", "data/articles.csv")
OUT_HTML = os.getenv("PSAI_ARTICLES_HTML", "public/articles.html")

# --- HTML & CSS Templates ---

# Using the same consistent CSS as the other pages
CSS = """
:root { --fg:#0f172a; --muted:#64748b; --chip:#e2e8f0; }
*{box-sizing:border-box} body{font-family:ui-sans-serif,system-ui; color:var(--fg); margin:0; background:#fff}
main{max-width:1200px;margin:40px auto;padding:0 16px}
h1{font-size:28px;margin:0 0 8px}
.sub{color:var(--muted);margin-bottom:24px}
.tablewrap{overflow:auto;border:1px solid #e5e7eb;border-radius:12px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:10px 12px;border-bottom:1px solid #e5e7eb}
th{text-align:left;background:#f8fafc;font-weight:600}
.topnav{background:#0b1220;color:#e5e7eb;padding:10px 16px;display:flex;gap:14px;align-items:center}
.topnav a{color:#93c5fd;text-decoration:none}
.topnav a:hover{text-decoration:underline}
"""

HTML_HEAD = """
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>PSAI Articles</title>
<style>{css}</style>
</head><body>
<div class="topnav"><strong>PSAI</strong> · <a href="./">Home</a> · <a href="news_feed.html">News Feed</a> · <a href="sources.html">Sources</a> · <a href="sources_table.html">Table</a> · <a href="articles.html">Articles</a></div>
<main>
"""

HTML_FOOT = """
</main>
</body></html>
"""

def build_page(rows_html):
    """Builds the full HTML page for the articles list."""
    return HTML_HEAD.format(css=CSS) + f"""
  <h1>Recent Articles & Mentions</h1>
  <div class="sub">A list of recently discovered articles, blog posts, and other mentions related to AI coding tools. Automatically pruned to the last 15 days.</div>
  <div class="tablewrap">
    <table>
      <thead>
        <tr>
          <th>Date Added</th>
          <th>Title</th>
          <th>Source</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
""" + HTML_FOOT

def main():
    if not os.path.exists(IN_CSV):
        print(f"Articles file not found at {IN_CSV}. Skipping page generation.")
        # Create an empty page so the site link doesn't 404
        os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
        open(OUT_HTML, "w", encoding="utf-8").write(build_page("<tr><td colspan='4'>No articles found.</td></tr>"))
        return

    with open(IN_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Sort by date, most recent first
    rows.sort(key=lambda r: r.get("Date Added", ""), reverse=True)

    row_html_parts = []
    if not rows:
        row_html_parts.append("<tr><td colspan='4'>No articles found.</td></tr>")
    else:
        for r in rows:
            date = html.escape(r.get("Date Added", ""))
            title = html.escape(r.get("Tool", "")) # The 'Tool' column holds the title for articles
            source = html.escape(r.get("Source Type", "Unknown"))
            link = html.escape(r.get("Website URL", "#"))
            link_html = f'<a href="{link}" target="_blank" rel="noopener">{link}</a>' if link != "#" else "N/A"

            row_html_parts.append(f"""
            <tr>
              <td>{date}</td>
              <td>{title}</td>
              <td>{source}</td>
              <td>{link_html}</td>
            </tr>""")

    final_html = build_page("".join(row_html_parts))

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Built {os.path.basename(OUT_HTML)} with {len(rows)} articles.")

if __name__ == "__main__":
    main()
