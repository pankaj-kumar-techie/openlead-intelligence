# OpenLead Intelligence - User Guide

This guide explains how to use the framework to find and score B2B leads.

## 🚀 Quick Start: Scrape Any Website (Testing Mode)

If you want to quickly test the tool on a specific list of companies or a directory page, use the `--url` command.

**Command:**
```bash
python main.py --url "https://news.ycombinator.com/show" --output-file my_test_results --output-format excel
```

**What this does:**
1.  Visits the URL you provided.
2.  Automatically tries to find company names and links.
3.  Enriches them (finds tech stack, hiring intent).
4.  Scores them (High/Medium/Low priority).
5.  Saves the result to `output/my_test_results.xlsx`.

---

## 🔍 Standard Usage: Pre-configured Sources

Use built-in modules for reliable daily scraping.

**1. Scrape "Show HN" (Hacker News)**
Best for finding brand new dev tools and startups.
```bash
python main.py --sources product_hunt --max-companies 50
```
*(Note: 'product_hunt' source currently points to Hacker News for reliable demo data)*

**2. Scrape Clutch.co**
Best for finding agencies and service providers.
```bash
python main.py --sources clutch
```

**3. Run Everything**
```bash
python main.py --sources all --max-companies 20
```

---

## 📊 Understanding the Output

Open the generated **Excel file** in the `output/` folder.

-   **Sheet 1 (Companies)**: The full list of every company found.
-   **Sheet 2 (High Priority)**: Only the best leads (Lead Score > 70).
-   **Sheet 3 (Summary)**: Quick stats on how many companies are hiring or funded.

### Key Columns to Look At:
-   **Lead Score**: 0-100. Higher is better.
-   **Priority**: High / Medium / Low.
-   **Tech Stack**: Detected technologies (e.g., "React, Django, AWS").
-   **Hiring Intent**: "Yes" if they have open jobs.
