PSAI — Feed Refresh & Sources Pages

What this does
--------------
1) scripts/build_feed_from_log.py
   - Reads data/news_log.json, writes public/feed.json (JSON Feed 1.1) + public/rss.xml (RSS 2.0).
   - Injects a Sources link into public/index.html (idempotent).

2) scripts/build_sources_pages.py
   - Reads data/PSAI_FullField_Tracker.csv, writes public/sources.html (cards) + public/sources_table.html (table).
   - Filters to AI dev tools (agents/IDE/reviewer/orchestration/MCP), hides raw URLs behind tooltipped icons.
   - Also injects the Sources link into public/index.html.

Local run
---------
python3 scripts/build_feed_from_log.py
python3 scripts/build_sources_pages.py

GitHub Actions
--------------
- After your harvesting step:

  - name: Build feeds
    run: python scripts/build_feed_from_log.py

  - name: Build sources pages (cards + table)
    env:
      PSAI_INCLUDE_REGEX: "(agent|agentic|orchestr|mcp|ide|editor|review|code\\s*assistant)"
      PSAI_EXCLUDE_REGEX: "^(product\\s*hunt|reddit|hacker\\s*news|hn\\s*—|hn\\s*show|latentspace|ben['’]s\\s*bites|npm|pypi|docker\\s*hub)\\b"
      PSAI_MIN_STARS: "50"
    run: python scripts/build_sources_pages.py

Nested repo fix
---------------
If your repo path looks like prindle-sprick-ai/prindle-sprick-ai/, add:
  working-directory: prindle-sprick-ai
to those steps.
