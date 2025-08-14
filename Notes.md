# Repository Process and Data Flow

This document outlines the automated processes and data flow within this repository, which is designed to discover, track, and report on AI coding tools.

## Overview

The repository uses two coordinated GitHub Actions workflows to automate the entire process: `PSAI Full-Field Daily` and `PSAI DeepSweep Discovery`. These workflows are responsible for discovering new tools, updating information on existing tools, and building the static HTML pages that display this data. The final output is deployed to GitHub Pages.

## Core Components

### Data Files

-   **`data/tools.csv`**: This is the central source of truth for the list of tracked AI tools. It contains curated information such as tool name, category, repository URL, star count, etc. Both workflows read from and write to this file.
-   **`data/news_log.json`**: This file acts as a log for recent updates (e.g., new releases, changelogs) harvested from the tracked tools. It is the data source for the `news_feed.html` page.
-   **`data/candidates.json`**: A temporary file used by the discovery scripts. It holds a list of potential new tools found during a workflow run before they are merged into `data/tools.csv`.

### Scripts

-   **`scripts/discover.py`**: Scans various online sources (GitHub, Product Hunt, Reddit, etc.) to find new AI coding tools. It outputs its findings to `data/candidates.json`.
-   **`scripts/merge_candidates.py`**: Reads `data/candidates.json`, deduplicates the list against the existing tools in `data/tools.csv`, and appends any new, unique tools to `data/tools.csv`.
-   **`scripts/harvest.py`**: Reads the list of tools from `data/tools.csv` and checks their registered feed URLs (e.g., GitHub Releases RSS feeds) for any new updates. It writes these updates into `data/news_log.json`.
-   **`scripts/build_feed_from_log.py`**: Reads `data/news_log.json` and generates three output files in the `public/` directory:
    1.  `news_feed.html`: The main HTML page for viewing recent tool updates.
    2.  `feed.json`: A machine-readable JSON Feed of the news log.
    3.  `rss.xml`: An RSS 2.0 feed of the news log.
-   **`scripts/build_sources_pages.py`**: Reads `data/tools.csv` and generates two output files in the `public/` directory:
    1.  `sources.html`: A card-based view of all the tracked tools.
    2.  `sources_table.html`: A table-based view of all the tracked tools.

### Workflows

The two workflows in `.github/workflows/` are coordinated to prevent conflicts. They share a `concurrency` group named `psai-build`, which ensures that only one of them can run at a time. Both workflows are triggered on a daily schedule or on pushes to the `main` branch.

1.  **`psai-fullfield.yml` (PSAI Full-Field Daily):**
    -   Performs a "light" discovery of new tools and merges them into `tools.csv`.
    -   Runs the `harvest.py` script to get the latest updates for all tracked tools.
    -   Runs other scripts to update the status of tools in `tools.csv`.
    -   Builds all the `public/` HTML, JSON, and XML files from the updated data sources.
    -   Commits all changes to `data/` and `public/` back to the `main` branch.
    -   Deploys the final `public/` directory to GitHub Pages.

2.  **`psai-deepsweep.yml` (PSAI DeepSweep Discovery):**
    -   Performs a more intensive "deep sweep" discovery of new tools from a wider range of sources.
    -   Merges these new candidates directly into `tools.csv`.
    -   Builds all the `public/` HTML, JSON, and XML files.
    -   Commits all changes back to the `main` branch.
    -   Deploys the final `public/` directory to GitHub Pages.

By having both workflows build and deploy the site after any data change, the live GitHub Pages site should always be up-to-date with the latest information in the repository.
