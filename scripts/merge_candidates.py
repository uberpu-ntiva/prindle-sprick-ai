#!/usr/bin/env python
import csv, json, re, sys, io, os
from urllib.parse import urlparse
from datetime import datetime, timezone

# I/O Configuration
IN_CANDIDATES = "data/candidates.json"
IN_TOOLS      = "data/tools.csv"
IN_ARTICLES   = "data/articles.csv"
OUT_TOOLS     = IN_TOOLS
OUT_ARTICLES  = IN_ARTICLES

# --- Classification Logic ---

# Domains that are likely to be articles/blogs/news, not dedicated tool pages.
ARTICLE_HOST_PATTERNS = [
    r"techcrunch\.com", r"venturebeat\.com", r"theverge\.com", r"arstechnica\.com",
    r"medium\.com", r"github\.blog", r"youtube\.com", r"youtu\.be",
    r"reddit\.com", r"news\.ycombinator\.com", r"forbes\.com", r"bloomberg\.com",
    r"huggingface\.co", # Often papers/blog posts, not the tool's primary site
    r"arxiv\.org", r"producthunt\.com", r"latent\.space", r"bensbites\.co"
]
ARTICLE_HOST_RX = re.compile(r"|".join(ARTICLE_HOST_PATTERNS), re.I)

# Titles that suggest an article, not a product name.
ARTICLE_TITLE_PATTERNS = [
    r"show hn", r"ask hn", r"launch hn", r"how to", r"tutorial", r"guide",
    r"deep dive", r"introduction to", r"announcing", r"introducing",
    r"vs\.", r"versus", r"case study"
]
ARTICLE_TITLE_RX = re.compile(r"|".join(ARTICLE_TITLE_PATTERNS), re.I)

def is_tool(candidate):
    """
    Classifies a candidate as a Tool or an Article based on heuristics.
    """
    tool_name = candidate.get("tool", "").lower()
    repo_url = candidate.get("repo_url", "")
    website_url = candidate.get("website_url", "")

    # Definite Tool: It has a code repository.
    if repo_url and "github.com" in repo_url:
        return True

    # Likely Article: The title matches common article patterns.
    if ARTICLE_TITLE_RX.search(tool_name):
        return False

    # Likely Article: The main link is to a known blog/news/aggregator site.
    if website_url:
        try:
            hostname = urlparse(website_url).hostname or ""
            if ARTICLE_HOST_RX.search(hostname):
                return False
        except Exception:
            pass # Ignore malformed URLs

    # Heuristic: If it has a website and a short name, it's probably a tool.
    if website_url and len(tool_name.split()) <= 5:
        return True

    # Default to classifying as an article if unsure.
    return False

# --- CSV Handling ---

# Define the column order for both CSVs.
# Articles will have fewer populated columns, but a consistent structure is good.
FIELDNAMES = ["Tool","Moniker","Category","Severity","RSS Available","Feed URL","Tracking Method",
              "Repo URL","Repo Status","Stars","Contributors","Docs URL","Website URL",
              "Source Type","Discovery Method","Launch Status","Last Seen Update","Status", "Date Added"]

def load_csv_to_set(path):
    """Loads a CSV and returns a set of (Tool, Moniker) tuples for fast deduplication."""
    if not os.path.exists(path):
        return set(), []
    try:
        with open(path, encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            rows = list(rdr)
            key_of = lambda r: ((r.get("Tool") or "").strip().lower(), (r.get("Moniker") or "").strip().lower())
            return {key_of(r) for r in rows}, rows
    except Exception:
        return set(), []

def monikerize(name):
    return re.sub(r"[^a-z0-9]+","-", (name or "").lower()).strip("-")

def save_csv(path, rows):
    """Saves a list of dicts to a CSV file with a consistent header."""
    if not rows:
        print(f"No new rows to save for {os.path.basename(path)}.")
        return

    # Ensure all rows contain all keys from the header.
    clean_rows = []
    for r in rows:
        clean_rows.append({k: r.get(k, "") for k in FIELDNAMES})

    # Check if file exists to decide on writing header
    file_exists = os.path.exists(path)

    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists or f.tell() == 0:
            w.writeheader()
        w.writerows(clean_rows)

# --- Main Logic ---

def main():
    # Load existing data for deduplication
    seen_tools, _ = load_csv_to_set(IN_TOOLS)
    seen_articles, _ = load_csv_to_set(IN_ARTICLES)

    # Load new candidates
    try:
        with open(IN_CANDIDATES, "r", encoding="utf-8") as f:
            candidates = json.load(f).get("items", [])
    except (FileNotFoundError, json.JSONDecodeError):
        print("No candidates found or candidates file is invalid.")
        candidates = []

    new_tools = []
    new_articles = []

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for cand in candidates:
        tool_name = (cand.get("tool") or "").strip()
        if not tool_name:
            continue

        moniker = (cand.get("moniker") or monikerize(tool_name))

        # Deduplicate against both existing lists
        key = (tool_name.lower(), moniker.lower())
        if key in seen_tools or key in seen_articles:
            continue

        # Prepare the base data row
        row = {
            "Tool": tool_name,
            "Moniker": moniker,
            "Category": cand.get("category","Discovery"),
            "Severity": "Minor",
            "RSS Available": "✅" if cand.get("feed_url") else "❌",
            "Feed URL": cand.get("feed_url",""),
            "Repo URL": cand.get("repo_url",""),
            "Website URL": cand.get("website_url",""),
            "Source Type": cand.get("source_type",""),
            "Discovery Method": "Auto-Discovery",
            "Date Added": today
        }

        # Classify and append
        if is_tool(cand):
            row["Tracking Method"] = "RSS" if row["Feed URL"] else "GitHub Releases"
            row["Repo Status"] = "Active" if row["Repo URL"] else ""
            new_tools.append(row)
            seen_tools.add(key)
        else:
            row["Category"] = "Article"
            row["Tracking Method"] = "HTML/Blog"
            new_articles.append(row)
            seen_articles.add(key)

    # Save the results
    if new_tools:
        save_csv(OUT_TOOLS, new_tools)
        print(f"Appended {len(new_tools)} new tool(s) to {os.path.basename(OUT_TOOLS)}.")
    else:
        print("No new tools to append.")

    if new_articles:
        save_csv(OUT_ARTICLES, new_articles)
        print(f"Appended {len(new_articles)} new article(s) to {os.path.basename(OUT_ARTICLES)}.")
    else:
        print("No new articles to append.")

if __name__ == "__main__":
    main()
