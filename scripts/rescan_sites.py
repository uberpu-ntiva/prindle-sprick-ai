import os, csv, re, requests
from bs4 import BeautifulSoup

TOOLS_PATH = os.getenv("PSAI_TOOLS_CSV", "data/tools.csv")
FILTERS_PATH = os.getenv("PSAI_FILTERS_CSV", "data/filters.csv")
HEADERS = {"User-Agent": "psai-rescan/1.0"}

def load_csv(path):
    if not os.path.exists(path): return []
    return list(csv.DictReader(open(path, 'r', encoding='utf-8')))

def save_csv(path, data, headers):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

def main():
    tools = load_csv(TOOLS_PATH)
    filters = load_csv(FILTERS_PATH)
    if not tools or not filters:
        print("Missing tools or filters CSV. Skipping.")
        return

    approved_tools = [t for t in tools if t.get('Status', '').lower() != 'pending_review' and t.get('Website URL')]
    include_rx = re.compile(next((f['pattern'] for f in filters if f['type'] == 'include'), '.*'), re.I)
    exclude_rx = re.compile(next((f['pattern'] for f in filters if f['type'] == 'exclude'), '^$'), re.I)

    existing_urls = {t['Website URL'] for t in tools if t.get('Website URL')}
    existing_names = {t['Tool'].lower() for t in tools}

    new_candidates = []
    print(f"Scanning {len(approved_tools)} approved tool websites...")

    for tool in approved_tools:
        url = tool.get('Website URL')
        print(f" -> Scanning {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')

            for a in soup.find_all('a', href=True):
                link_text = a.get_text(strip=True)
                link_href = a['href']

                if not link_text or not link_href.startswith('http'):
                    continue

                if include_rx.search(link_text) and not exclude_rx.search(link_text):
                    if link_href in existing_urls or link_text.lower() in existing_names:
                        continue

                    moniker = re.sub(r'[^a-z0-9]+', '-', link_text.lower()).strip('-')
                    candidate = {
                        'Tool': link_text,
                        'Moniker': moniker,
                        'Website URL': link_href,
                        'Status': 'pending_review',
                        'Discovery Method': 'site_rescan',
                        'Source Type': 'Scraped',
                        'Category': 'pending_review'
                    }

                    # Avoid adding duplicates in the same run
                    if candidate['Website URL'] not in {c['Website URL'] for c in new_candidates}:
                        new_candidates.append(candidate)
                        existing_urls.add(candidate['Website URL']) # Add to set to prevent re-adding
                        print(f"    + Found potential new tool: {link_text} ({link_href})")

        except requests.RequestException as e:
            print(f"    ! Could not fetch {url}: {e}")

    if new_candidates:
        print(f"\nFound {len(new_candidates)} new candidates. Appending to tools file.")
        all_tools_updated = tools + new_candidates
        tool_headers = tools[0].keys() if tools else new_candidates[0].keys()
        # Fill in missing keys for new candidates
        for c in new_candidates:
            for h in tool_headers:
                if h not in c:
                    c[h] = ''
        save_csv(TOOLS_PATH, all_tools_updated, tool_headers)
    else:
        print("\nNo new candidates found.")

if __name__ == "__main__":
    main()
