#!/usr/bin/env python
import os, re, json, csv, requests
from xml.etree import ElementTree as ET

SOURCES_PATH = os.getenv("PSAI_SOURCES_CSV", "data/sources.csv")
FILTERS_PATH = os.getenv("PSAI_FILTERS_CSV", "data/filters.csv")
TOOLS_PATH = os.getenv("PSAI_TOOLS_CSV", "data/tools.csv")
CANDIDATES_PATH = os.getenv("PSAI_CANDIDATES_JSON", "data/candidates.json")
HEADERS = {"User-Agent": "psai-discover/2.0"}

def load_csv(path):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def fetch_and_parse_rss(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        items = []
        for item in root.findall('.//item'):
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            items.append({'title': title, 'link': link})
        # Also try Atom format
        if not items:
            ns = {'a': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('.//a:entry', ns):
                title = entry.find('a:title', ns).text or ''
                link = entry.find('a:link', ns).get('href') or ''
                items.append({'title': title, 'link': link})
        return items
    except Exception as e:
        print(f"Error fetching/parsing {url}: {e}")
        return []

def main():
    sources = load_csv(SOURCES_PATH)
    filters = load_csv(FILTERS_PATH)
    tools = load_csv(TOOLS_PATH)

    include_rx = re.compile(next((f['pattern'] for f in filters if f['type'] == 'include'), '.*'), re.I)
    exclude_rx = re.compile(next((f['pattern'] for f in filters if f['type'] == 'exclude'), '^$'), re.I)

    existing_tools_by_url = {t['Website URL'] for t in tools if t.get('Website URL')}
    existing_tools_by_name = {t['Tool'].lower() for t in tools}

    candidates = []
    for source in sources:
        url = source.get('Feed URL')
        if not url or source.get('Tracking Method') != 'RSS':
            continue

        print(f"Scanning source: {source['Tool']}")
        items = fetch_and_parse_rss(url)
        for item in items:
            title = item.get('title', '')
            link = item.get('link', '')
            if link in existing_tools_by_url:
                continue
            if title.lower() in existing_tools_by_name:
                continue

            if include_rx.search(title) and not exclude_rx.search(title):
                moniker = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                candidate = {
                    "tool": title,
                    "moniker": moniker,
                    "category": "pending_review",
                    "website_url": link,
                    "source_type": source.get("Source Type"),
                    "status": "pending_review"
                }
                if candidate not in candidates:
                    candidates.append(candidate)
                    print(f"  + Found candidate: {title}")

    with open(CANDIDATES_PATH, 'w', encoding='utf-8') as f:
        json.dump({"items": candidates}, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(candidates)} new candidates to {CANDIDATES_PATH}")

if __name__ == "__main__":
    main()
