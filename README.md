# PSAI - AI Coding Tools Tracker

This repository contains an automated system for discovering, tracking, and reporting on AI coding tools.

## Overview

The system is powered by a set of Python scripts and orchestrated by two GitHub Actions workflows. It automatically:
1.  Discovers new AI coding tools from various online sources.
2.  Tracks them in a central CSV file (`data/tools.csv`).
3.  Harvests recent updates and release notes for these tools.
4.  Builds a static website in the `public/` directory with the latest data.
5.  Deploys the website to GitHub Pages.

## Documentation

For a complete, detailed explanation of the entire data flow, build process, and workflow automation, please see **[Notes.md](Notes.md)**.

For instructions targeted at AI agents working on this repository, please see **[AGENTS.md](AGENTS.md)**.

---

## System Analysis

This section provides a detailed analysis of the repository's structure, data workflow, and file usage.

### 1. Script and Data Workflow Hierarchy

This outlines the entire automated workflow, from data collection to website generation, as defined in `.github/workflows/main.yml`.

#### **Phase 1: Data Initialization**
*   **Action**: Creates initial data files if they don't exist.
*   **Outputs**:
    *   `data/tools.csv` (from `data/init_tools.csv`)
    *   `data/articles.csv` (empty file)
    *   `data/sources.csv` (from `data/init_sources.csv`)
    *   `data/filters.csv` (from `data/init_filters.csv`)

#### **Phase 2: Data Collection & Processing**

*   **Step 1: Discovery (Deep Sweep)**
    *   **Script**: `scripts/discover.py`
    *   **Purpose**: Scans multiple sources (Product Hunt, GitHub, Reddit, etc.) to find potential new AI coding tools.
    *   **Inputs**: Command-line flags (`--product-hunt`, `--github`, etc.) specify which sources to scan.
    *   **Output**: `data/candidates.json` - A raw list of potential tools.

*   **Step 2: Categorize & Merge Candidates**
    *   **Script**: `scripts/merge_candidates.py`
    *   **Purpose**: Classifies candidates as either "tools" or "articles" and adds new, unique entries to the appropriate data files.
    *   **Inputs**: `data/candidates.json`, `data/tools.csv`, `data/articles.csv`
    *   **Outputs (Appends to)**: `data/tools.csv`, `data/articles.csv`

*   **Step 3: Prune Old Articles**
    *   **Script**: `scripts/prune_articles.py`
    *   **Purpose**: Removes entries from the articles list older than 15 days.
    *   **Input**: `data/articles.csv`
    *   **Output**: `data/articles.csv` (modified)

*   **Step 4: Harvest News from Tools**
    *   **Script**: `scripts/harvest.py`
    *   **Purpose**: Checks RSS feeds or GitHub release pages of tracked tools for updates.
    *   **Inputs**: `data/tools.csv`, `data/sources.csv`
    *   **Output**: `data/news_log.json`

*   **Step 5: Update Tracker Status**
    *   **Script**: `scripts/update_tracker.py`
    *   **Purpose**: Updates status information for tools based on the latest news.
    *   **Inputs**: `data/tools.csv`, `data/news_log.json`
    *   **Output**: `data/tools.csv` (modified)

*   **Step 6: Re-scan Tool Websites**
    *   **Script**: `scripts/rescan_sites.py`
    *   **Purpose**: Scans websites of existing tools for links to other potential tools.
    *   **Inputs**: `data/tools.csv`, `data/filters.csv`
    *   **Output**: `data/tools.csv` (appends new candidates with `pending_review` status).

#### **Phase 3: Website Build**

*   **`scripts/build_feed_from_log.py`**:
    *   **Input**: `data/news_log.json`
    *   **Outputs**: `public/news_feed.html`, `public/feed.json`, `public/rss.xml`
*   **`scripts/build_articles_page.py`**:
    *   **Input**: `data/articles.csv`
    *   **Output**: `public/articles.html`
*   **`scripts/build_sources_pages.py`**:
    *   **Inputs**: `data/tools.csv`, `data/news_log.json`
    *   **Outputs**: `public/index.html`, `public/sources.html`, `public/sources_table.html`

#### **Phase 4: Alerting & Deployment**
*   An in-line script checks `data/news_log.json` for major updates and creates a GitHub Issue if needed.
*   The workflow commits all changes in `data/` and `public/` to the repository.
*   The `public/` directory is deployed to GitHub Pages.

---

### 2. Data Flowchart and Website Navigation

#### **Data Flow Summary**
1.  **Seed**: `init_*.csv` files initialize the core data files (`tools.csv`, `sources.csv`, etc.).
2.  **Discover**: `discover.py` creates `candidates.json`.
3.  **Merge**: `merge_candidates.py` processes `candidates.json` into `tools.csv` and `articles.csv`.
4.  **Harvest**: `harvest.py` uses `tools.csv` to create `news_log.json`.
5.  **Update**: `update_tracker.py` uses `news_log.json` to modify `tools.csv`.
6.  **Build**: The `build_*.py` scripts use the final CSV and JSON files to generate the static website in `public/`.

#### **Website Navigation**
The navigation bar is consistent across all pages and links to the following, all of which are in the `public/` directory:

*   **Home** (`index.html`): Dashboard with recent updates and new tools. Generated by `scripts/build_sources_pages.py`.
*   **News Feed** (`news_feed.html`): A chronological list of all tool updates. Generated by `scripts/build_feed_from_log.py`.
*   **Sources** (`sources.html`): A card-based view of all tracked tools. Generated by `scripts/build_sources_pages.py`.
*   **Table** (`sources_table.html`): A table view of all tracked tools. Generated by `scripts/build_sources_pages.py`.
*   **Articles** (`articles.html`): A list of recent articles and mentions. Generated by `scripts/build_articles_page.py`.

---

### 3. Unused Files

The following files were identified as being unused by the current automated workflow:

*   `build_feed.py`: Old feed generation script. The workflow uses `scripts/build_feed_from_log.py`.
*   `index.html` (root): Old, static homepage. The site uses the generated `public/index.html`.
*   `news_log.json` (root): Old data file. The workflow uses `data/news_log.json`.
*   `rss.xml` (root): Old build artifact. The workflow generates `public/rss.xml`.
*   `feed.json` (root): Old build artifact. The workflow generates `public/feed.json`.
*   `data/ugh.txt`: Temporary or junk file.
*   `data/sources.yaml`: An alternative data format for sources that is not used. The system uses CSV files.
