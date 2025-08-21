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
