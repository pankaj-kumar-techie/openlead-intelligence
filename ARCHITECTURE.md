# OpenLead Intelligence - Architecture & Internal Mechanics

## 1. High-Level Overview
OpenLead Intelligence is a **modular, event-driven pipeline** designed to transform raw, unstructured web data into structured, scored business intelligence. It follows a classic **ETL (Extract, Transform, Load)** pattern, adapted for real-time web intelligence.

### Core Value Proposition (Benefits)

| Stakeholder | Benefit |
| :--- | :--- |
| **Sales Teams** | **High-Intent Leads**: Receive a prioritized list of companies actively hiring or growing, saving hours of manual prospecting. |
| **Market Researchers** | **Trend Analysis**: Aggregate tech stacks and funding data to spot emerging market trends. |
| **Recruiters** | **Hiring Signals**: Identify companies with sudden spikes in job postings. |
| **Developers** | **Extensibility**: Plug-and-play architecture allows adding new sources (e.g., Reddit, LinkedIn) in under 1 hour. |

---

## 2. Internal Architecture

The framework consists of four primary layers:
1.  **Collection Layer (Extract)**
2.  **Enrichment Layer (Transform)**
3.  **Scoring Layer (Analyze)**
4.  **Orchestration Layer (Manage)**

### 2.1 Collection Layer (`collectors/`)
This layer is responsible for interfacing with the external world.
-   **BaseScraper**: The abstract parent class. It handles:
    -   **Politeness**: Rate limiting (`time.sleep`) and User-Agent rotation.
    -   **Resilience**: Intelligent retry logic with exponential backoff for network errors (403/500 codes).
    -   **Compliance**: Checks `robots.txt` automatically.
-   **Source-Specific Scrapers**:
    -   `ProductHuntScraper`: Parses HTML for new launches.
    -   `ClutchScraper`: Iterates through pagination to gather B2B profiles.
    -   `SeleniumScraper`: Spawns a headless Chrome instance to render JavaScript for complex sites.

### 2.2 Enrichment Layer (`enrichment/`)
Raw data is often incomplete. The enrichment layer "fills in the blanks" by visiting company websites and analyzing secondary signals.
-   **TechStackDetector**: Downloads the company's homepage HTML and scans for 50+ unique signatures (e.g., `wp-content` -> WordPress, `react-root` -> React).
-   **HiringIntent**: (Concept) Visits `/careers` pages to count open roles.
-   **DomainEnricher**: Resolves DNS records to approximate hosting location.

### 2.3 Scoring Layer (`scoring/`)
This is the brain of the operation. It assigns a numerical value (0-100) to each lead.
-   **LeadScorer**: Uses a weighted algorithm:
    -   `35%` Intent (Hiring volume, recent news)
    -   `30%` Fit (Company size, industry)
    -   `20%` Tech Stack (Relevance to your product)
    -   `15%` Engagement (Social presence)
-   **RulesEngine**: Allows hard-coded "If-This-Then-That" logic (e.g., "Always flag companies using Django").

### 2.4 Orchestration Layer (`pipeline/`)
The conductor that synchronizes everything.
-   **PipelineOrchestrator**:
    1.  Spawns threads for parallel scraping.
    2.  Aggregates results into a single list.
    3.  **Deduplication**: Removes duplicate companies (e.g., "Acme Inc" vs "Acme Inc.") using fuzzy string matching.
    4.  Passes data to Enrichers → Scorers → Exporters.
-   **DataExporter**: Validates data against Pydantic models and writes to CSV, JSON, or Excel.

---

## 3. Data Flow Diagram

```mermaid
graph TD
    A[Start Pipeline] --> B{Parallel Collection}
    B --> C[Product Hunt Scraper]
    B --> D[Clutch Scraper]
    B --> E[AngelList Scraper]
    C --> F[Raw Data Pool]
    D --> F
    E --> F
    F --> G[Deduplication Engine]
    G --> H{Parallel Enrichment}
    H --> I[Tech Stack Detection]
    H --> J[DNS Analysis]
    H --> K[Hiring Intent]
    I --> L[Enriched Data]
    J --> L
    K --> L
    L --> M[Scoring Engine]
    M --> N[Filter (< Threshold)]
    N --> O[Export (CSV/Excel)]
```

## 4. Key Design Decisions

-   **Pydantic Models**: We use strong typing (`models/schemas.py`) to ensure data integrity. If a scraper returns a string for "employee_count", Pydantic validation handles variables or throws a clear error.
-   **Factory Pattern**: Scrapers are instantiated dynamically based on configuration, making the main loop clean and agnostic to the specific sources.
-   **Decorator Pattern**: Retry logic (`@retry_on_exception`) and rate limiting are applied as decorators, keeping the core business logic clean.

## 5. Security & Ethics Compliance
-   **No PII Storage**: The schema focuses on *Company* entities, not *Person* entities, minimizing GDPR risk.
-   **Audit Logging**: The `logger` module tracks every request, making it easy to audit what sites were accessed and when.
