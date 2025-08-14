# Agent Instructions

This document provides instructions for AI agents working on this repository.

## Overview

This repository is an automated system for tracking and reporting on AI coding tools. The entire process is managed by two GitHub Actions workflows located in `.github/workflows/`. These workflows run Python scripts from the `scripts/` directory to discover new tools, update data files in the `data/` directory, and build the static website into the `public/` directory.

## Key Files and Scripts

-   **Primary Data Source:** The single source of truth for the list of tracked tools is `data/tools.csv`. All discovery and update processes should ultimately write to this file.
-   **News Feed Data:** The news feed is built from `data/news_log.json`.
-   **Build Scripts:**
    -   `scripts/build_feed_from_log.py` generates `public/news_feed.html` and its associated JSON/RSS feeds.
    -   `scripts/build_sources_pages.py` generates `public/sources.html` and `public/sources_table.html`.
-   **Workflows:** The workflows in `.github/workflows/` define the end-to-end process. Any changes to the build logic or data flow will likely require modifying these files.

## Agent Directives

1.  **Maintain Consistency:** The two workflows, `psai-fullfield.yml` and `psai-deepsweep.yml`, must remain consistent in how they handle data and build the site. Both should use `data/tools.csv` as the primary tracker and build all site pages after any data modification.
2.  **Test via Workflow:** The most reliable way to test changes is to observe the execution of the GitHub Actions workflows. The build process is complex and dependent on the workflow environment.
3.  **Post-Merge Verification:** After a pull request is merged to `main`, the `fullfield` and `deepsweep` workflows will automatically trigger. It is the responsibility of the acting agent to monitor these workflow runs to ensure they complete successfully and that the deployment to GitHub Pages reflects the changes.
4.  **Agent Action Log:** For every agent run that results in a code change, you must record your actions and the triggered workflow run in a log. This is to ensure a clear audit trail and to assist in debugging future issues.
