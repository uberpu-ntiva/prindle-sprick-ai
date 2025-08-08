import json, os, datetime, email.utils

SITE_URL = os.environ.get("SITE_URL", "https://<your-github-username>.github.io/ai-tools-news")
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4)))
http_date = email.utils.format_datetime(now)

with open("news_log.json", "r", encoding="utf-8") as f:
    data = json.load(f)
items = data.get("items", [])

# --- Build RSS ---
rss_items = []
for it in items:
    guid = f"{it['date']}-{it['tool'].lower().replace(' ','-')}-{it['headline'].split()[0].lower()}"
    title = f"[{it['tool']}] {it['headline']}"
    description = f"{it['severity']} — {it['impact']} Moniker: \"{it['moniker']}\""
    pub_date = email.utils.format_datetime(datetime.datetime.fromisoformat(it['date'] + "T09:20:00-04:00"))
    link = it.get("link") or f"{SITE_URL}/?q={it['moniker'].replace(' ', '+')}"
    category = it.get("category", "Updates")
    rss_items.append(f"""
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid isPermaLink=\"false\">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <category>{category}</category>
      <description>{description}</description>
    </item>""")

rss_xml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\" xmlns:atom=\"http://www.w3.org/2005/Atom\">\n  <channel>\n    <title>AI Coding Tools — 30-Day Changes & News</title>\n    <link>{SITE_URL}</link>\n    <description>Rolling updates (last 30 days) for AI coding tools, agents, orchestrators, and MCP implementations. Source: AI Coding Tools Project.</description>\n    <language>en-us</language>\n    <generator>GitHub Actions — build_feed.py</generator>\n    <ttl>30</ttl>\n    <atom:link href=\"{SITE_URL}/rss.xml\" rel=\"self\" type=\"application/rss+xml\" />\n    <lastBuildDate>{http_date}</lastBuildDate>\n    {''.join(rss_items)}\n  </channel>\n</rss>"""

with open("rss.xml", "w", encoding="utf-8") as f:
    f.write(rss_xml)

# --- Build JSON Feed (v1) ---
json_items = []
for it in items:
    json_items.append({
        "id": f"{it['date']}-{it['tool'].lower().replace(' ', '-')}",
        "url": it.get("link") or f"{SITE_URL}/?q={it['moniker'].replace(' ', '+')}",
        "title": f"[{it['tool']}] {it['headline']}",
        "content_text": f"{it['severity']} — {it['impact']} Moniker: '{it['moniker']}'",
        "date_published": f"{it['date']}T09:20:00-04:00",
        "tags": [it.get("category", "Updates"), it.get("severity", "Minor")]
    })

feed = {
    "version": "https://jsonfeed.org/version/1",
    "title": "AI Coding Tools — 30-Day Changes & News",
    "home_page_url": SITE_URL,
    "feed_url": f"{SITE_URL}/feed.json",
    "items": json_items
}

with open("feed.json", "w", encoding="utf-8") as f:
    json.dump(feed, f, ensure_ascii=False, indent=2)
print("Generated rss.xml and feed.json")
