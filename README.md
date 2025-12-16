# OpenLead Intelligence Framework

A production-ready, modular Python framework for B2B lead intelligence, web scraping, and data enrichment.

## Features

- **Multi-Source Scraping**:
    - Product Hunt (New launches)
    - AngelList / Wellfound (Startups & Hiring)
    - Clutch.co (B2B Services)
    - *Extensible for LinkedIn, Indeed, etc.*
- **Intelligent Enrichment**:
    - Tech Stack Detection (analyze website source code)
    - Hiring Intent Analysis
    - Domain & DNS Intelligence
- **Lead Scoring**:
    - Configurable rules engine
    - Scored on Intent, Fit, Tech Stack, and Engagement
    - Priority classification (High/Medium/Low)
- **Production Grade**:
    - Automatic Retry & Error Handling
    - Rate Limiting & User-Agent Rotation
    - Deduplication Pipeline
    - Type-Safe Data Models (Pydantic)
    - structured Logging

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/openlead-intelligence.git
   cd openlead-intelligence
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**:
   Copy the example environment file and edit it.
   ```bash
   cp .env.example .env
   ```

## Usage

### Quick Start

Run the full pipeline with default settings (scrapes Product Hunt):

```bash
python main.py
```

### Advanced Usage

Scrape specific sources with custom limits and output formats:

```bash
# Scrape Product Hunt and AngelList, get 50 companies each
python main.py --sources product_hunt angellist --max-companies 50

# Export to Excel with Lead Scores
python main.py --output-format excel --output-file lead_report_2024 --enable-scoring
```

### Library Usage

You can use individual modules in your own scripts:

```python
from collectors.product_hunt import ProductHuntScraper
from enrichment.tech_stack import TechStackDetector

# Scrape
scraper = ProductHuntScraper()
result = scraper.scrape(days_back=1)

# Enrich
detector = TechStackDetector()
for company in result.companies:
    detector.enrich_company(company)
    print(f"{company.name} uses: {company.enrichment.tech_stack.frameworks}")
```

## Project Structure

```text
openlead-intelligence/
├── collectors/         # Scraping modules (ProductHunt, AngelList, etc.)
├── enrichment/         # Data enrichment (Tech stack, hiring intent)
├── models/             # Pydantic data schemas
├── pipeline/           # Orchestrator, Deduplication, Export
├── scoring/            # Lead scoring logic
├── utils/              # Logging, Helpers, Config
├── main.py             # CLI Entry point
└── config.py           # Configuration management
```

## Legal & Ethics

Please read [LEGAL.md](LEGAL.md) before using this tool. This framework is designed for **public data only**.

- Respect `robots.txt`.
- Do not scrape personal private data.
- Adhere to rate limits to avoid stressing target servers.
