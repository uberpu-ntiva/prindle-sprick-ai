#!/usr/bin/env python
import argparse, os, json, csv, re
from datetime import datetime, timedelta, timezone
import requests
from xml.etree import ElementTree as ET
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

TZ = timezone.utc
NOW = datetime.now(TZ)
CUTOFF = NOW - timedelta(days=30)
HEADERS = {"User-Agent": "psai/1.3"}

def ensure_aware(dt):
    # Force timezone-aware (UTC) datetimes
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def iso_date(s, fallback=None):
    """Parse many date shapes into a TZ-aware UTC datetime."""
    if not s:
        return ensure_aware(fallback or NOW)
    s = str(s).strip()
    # Try ISO first (including trailing 'Z')
    try:
        if s.endswith('Z'):
            dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
            return ensure_aware(dt)
        # Bare date like 2025-08-11
        if len(s) == 10 and s[4] == '-' and s[7] == '-':
            dt = datetime.strptime(s, "%Y-%m-%d")
            return ensure_aware(dt)
        # Generic ISO (may be naive)
        dt = datetime.fromisoformat(s)
        return ensure_aware(dt)
    except Exception:
        pass
    # RSS/HTTP formats
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",       # ISO with tz
        "%Y-%m-%dT%H:%M:%S",         # ISO without tz
        "%Y-%m-%d"                   # date only
    ]:
        try:
            dt = datetime.strptime(s, fmt)
            return ensure_aware(dt)
        except Exception:
            continue
    return ensure_aware(fallback or NOW)

def load_json(path, default):
    return json.load(open(path, "r", encoding="utf-8")) if os.path.exists(path) else default

def save_json(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def from_github_releases(repo):
    url = f"https://api.github.com/repos/{repo}/releases"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    out = []
    for rel in r.json():
        dt = rel.get("published_at") or rel.get("created_at") or NOW.isoformat()
        when = iso_date(dt, NOW)
        out.append({
            "date": when.strftime("%Y-%m-%d"),
            "headline": rel.get("name") or rel.get("tag_name") or "Release",
            "link": rel.get("html_url")
        })
    return out

def from_rss(url):
    try:
        text = fetch(url)
        # Clean up common XML issues like unescaped ampersands before parsing
        text = re.sub(r'&(?![a-zA-Z]+;|#[0-9]+;)', '&amp;', text)
        root = ET.fromstring(text)
        items = []
    except (requests.RequestException, ET.ParseError) as e:
        print(f"  ! Failed to fetch/parse RSS feed {url}: {e}")
        return []
    # Try RSS
    for it in root.findall("./channel/item"):
        title = it.findtext("title") or "Update"
        link = it.findtext("link") or ""
        pub  = it.findtext("pubDate") or it.findtext("date") or ""
        when = iso_date(pub, NOW)
        items.append({"date": when.strftime("%Y-%m-%d"), "headline": title.strip(), "link": link.strip()})
    # Try Atom as well
    if not items:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for it in root.findall(".//a:entry", ns):
            title_el = it.find("a:title", ns)
            title = (title_el.text if title_el is not None else "Update").strip()
            link_el = it.find("a:link", ns)
            link = link_el.get("href") if link_el is not None else ""
            pub_el = it.find("a:updated", ns) or it.find("a:published", ns)
            pub = pub_el.text if pub_el is not None else ""
            when = iso_date(pub, NOW)
            items.append({"date": when.strftime("%Y-%m-%d"), "headline": title, "link": link})
    return items

def from_html(cfg):
    if not BeautifulSoup:
        return []
    soup = BeautifulSoup(fetch(cfg["url"]), "html.parser")
    out = []
    for art in soup.select(cfg.get("item_selector","article"))[:20]:
        ttl = art.select_one(cfg.get("title_selector","h2, h3"))
        lnk = art.select_one(cfg.get("link_selector","a"))
        dte = art.select_one(cfg.get("date_selector","time, .date"))
        title = ttl.get_text(strip=True) if ttl else "Update"
        link = (lnk.get("href") if lnk else cfg["url"]) or cfg["url"]
        if link and not str(link).startswith("http"):
            link = cfg["url"]
        date = (dte.get("datetime") if dte else "") or ""
        when = iso_date(date, NOW)
        out.append({"date": when.strftime("%Y-%m-%d"), "headline": title, "link": link})
    return out

def classify_severity(text):
    t = (text or "").lower()
    if any(k in t for k in ["cve","vulnerability","security","rce","xss","patch"]): return "Security"
    if any(k in t for k in ["major","breaking","incident","outage","downtime","elevated errors","regression","launch","ga","v1.","v2.","released"]): return "Major"
    return "Minor"

def load_csv(path):
    if not os.path.exists(path): return []
    return list(csv.DictReader(open(path, 'r', encoding='utf-8')))

def save_log(log, path):
    log["items"].sort(key=lambda x: (x.get("date", ""), x.get("tool", "")), reverse=True)
    cutoff_date = (NOW - timedelta(days=30)).date().isoformat()
    log["items"] = [it for it in log["items"] if it.get("date", "") >= cutoff_date]
    save_json(path, log)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", required=True, help="Path to tools.csv")
    ap.add_argument("--sources", required=True, help="Path to sources.csv")
    ap.add_argument("--log", required=True, help="Path to news_log.json")
    args = ap.parse_args()

    tools = load_csv(args.tools)
    sources = load_csv(args.sources)
    log = load_json(args.log, {"items": []})
    existing = {(it.get("date"), it.get("tool"), it.get("headline")) for it in log.get("items", [])}

    approved_tools = [t for t in tools if t.get('Status') != 'pending_review']
    tool_names = {t['Tool'].lower() for t in approved_tools}
    tool_map = {t['Tool'].lower(): t for t in approved_tools}

    # Phase 1: Scan press sources for mentions of approved tools
    print("--- Phase 1: Scanning press sources ---")
    for source in sources:
        feed_url = source.get('Feed URL')
        if not feed_url: continue
        print(f"Scanning source: {source['Tool']}")
        for item in from_rss(feed_url):
            headline = item.get('headline', '')
            found_tool_name = next((name for name in tool_names if re.search(r'\b' + re.escape(name) + r'\b', headline, re.I)), None)
            if found_tool_name:
                tool_data = tool_map[found_tool_name]
                key = (item['date'], tool_data['Tool'], headline)
                if key in existing: continue

                print(f"  + Found mention of '{tool_data['Tool']}' in: {headline}")
                log["items"].append({
                    "date": item['date'],
                    "tool": tool_data['Tool'],
                    "moniker": tool_data.get('Moniker', ''),
                    "category": tool_data.get('Category', 'Updates'),
                    "severity": classify_severity(headline),
                    "headline": headline,
                    "link": item.get('link', ''),
                    "source": feed_url,
                })
                existing.add(key)

    # Phase 2: Scan direct tool feeds
    print("\n--- Phase 2: Scanning direct tool feeds ---")
    for tool in approved_tools:
        updates = []
        try:
            if tool.get('Feed URL') and tool['Feed URL'] != 'N/A':
                print(f"Scanning tool RSS: {tool['Tool']}")
                updates += from_rss(tool['Feed URL'])
            elif tool.get('Repo URL') and 'github.com' in tool['Repo URL']:
                print(f"Scanning tool GitHub Releases: {tool['Tool']}")
                repo_path = re.search(r'github\.com/([^/]+/[^/]+)', tool['Repo URL']).group(1)
                updates += from_github_releases(repo_path)
        except Exception as e:
            print(f"  ! Error processing {tool['Tool']}: {e}")
            continue

        for u in updates:
            key = (u['date'], tool['Tool'], u['headline'])
            if key in existing: continue

            log["items"].append({
                "date": u['date'],
                "tool": tool['Tool'],
                "moniker": tool.get('Moniker', ''),
                "category": tool.get('Category', 'Updates'),
                "severity": classify_severity(u['headline']),
                "headline": u['headline'],
                "link": u.get('link', ''),
                "source": tool.get('Feed URL') or tool.get('Repo URL'),
            })
            existing.add(key)

    save_log(log, args.log)
    print(f"\nHarvest complete. Log saved to {args.log}")

if __name__ == "__main__":
    main()
