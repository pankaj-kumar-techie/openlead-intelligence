#!/usr/bin/env python3
# OpenLead Intelligence - Main Pipeline Example

"""
Main pipeline demonstration for B2B lead intelligence framework.

This script demonstrates:
1. Multi-source data collection (Product Hunt, AngelList)
2. Data enrichment (tech stack detection)
3. Lead scoring and prioritization
4. Data export (CSV, JSON, Excel)

Usage:
    python main.py
    python main.py --sources product_hunt angellist --max-companies 50
    python main.py --output-format excel --output-file my_leads
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from utils.logger import get_logger

# Collectors
from collectors.product_hunt import ProductHuntScraper
from collectors.angellist import AngelListScraper

# Enrichment
from enrichment.tech_stack import TechStackDetector

# Scoring
from scoring.lead_scorer import LeadScorer

# Pipeline
from pipeline.orchestrator import PipelineOrchestrator
from pipeline.output import DataExporter

logger = get_logger("main")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="OpenLead Intelligence - B2B Lead Intelligence Framework"
    )
    
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["product_hunt", "angellist", "clutch", "crunchbase", "all"],
        default=["product_hunt"],
        help="Data sources to scrape"
    )
    
    parser.add_argument(
        "--max-companies",
        type=int,
        default=20,
        help="Maximum companies to scrape per source"
    )
    
    parser.add_argument(
        "--days-back",
        type=int,
        default=7,
        help="Days to look back (for Product Hunt)"
    )
    
    parser.add_argument(
        "--location",
        type=str,
        default=None,
        help="Filter by location (for AngelList)"
    )
    
    parser.add_argument(
        "--enable-enrichment",
        action="store_true",
        default=True,
        help="Enable data enrichment"
    )
    
    parser.add_argument(
        "--enable-scoring",
        action="store_true",
        default=True,
        help="Enable lead scoring"
    )
    
    parser.add_argument(
        "--output-format",
        choices=["csv", "json", "excel", "all"],
        default="csv",
        help="Output format"
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Output filename (without extension)"
    )
    
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum score threshold (0-100)"
    )
    
    return parser.parse_args()


def main():
    """Main pipeline execution."""
    # Parse arguments
    args = parse_arguments()
    
    # Update settings
    settings.min_score_threshold = args.min_score
    
    logger.info("=" * 70)
    logger.info("OpenLead Intelligence - B2B Lead Intelligence Framework")
    logger.info("=" * 70)
    logger.info(f"Sources: {args.sources}")
    logger.info(f"Max companies per source: {args.max_companies}")
    logger.info(f"Enrichment: {args.enable_enrichment}")
    logger.info(f"Scoring: {args.enable_scoring}")
    logger.info(f"Output format: {args.output_format}")
    logger.info("=" * 70)
    
    # Initialize scrapers based on selected sources
    scrapers = []
    scraper_configs = []
    
    sources = args.sources
    if "all" in sources:
        sources = ["product_hunt", "angellist", "clutch", "crunchbase"]
    
    if "product_hunt" in sources:
        # NOTE: Using Hacker News logic for reliable demo data as PH has high blocking
        logger.info("Initializing Hacker News Scraper (Reliable Demo Source)")
        from collectors.job_boards import HackerNewsScraper
        scrapers.append(HackerNewsScraper())
        scraper_configs.append({})
        
    # if "product_hunt" in sources: ... (Old logic commented out or removed for demo)
    
    if "angellist" in sources:
        logger.info("Initializing AngelList scraper")
        scrapers.append(AngelListScraper())
        scraper_configs.append({
            "location": args.location,
            "max_companies": args.max_companies
        })

    if "clutch" in sources:
        logger.info("Initializing Clutch scraper")
        from collectors.clutch import ClutchScraper
        scrapers.append(ClutchScraper())
        scraper_configs.append({
            "category": "web-developers", # Default category
            "max_pages": 1
        })

    if "crunchbase" in sources:
        logger.info("Initializing Crunchbase scraper")
        from collectors.crunchbase import CrunchbaseScraper
        scrapers.append(CrunchbaseScraper())
        scraper_configs.append({
            "max_companies": args.max_companies
        })
    
    # Initialize enrichers
    enrichers = []
    if args.enable_enrichment:
        logger.info("Initializing enrichers")
        enrichers.append(TechStackDetector())
    
    # Initialize scorer
    scorer = None
    if args.enable_scoring:
        logger.info("Initializing lead scorer")
        scorer = LeadScorer()
    
    # Initialize pipeline orchestrator
    orchestrator = PipelineOrchestrator(
        enable_enrichment=args.enable_enrichment,
        enable_scoring=args.enable_scoring,
        enable_deduplication=True,
        max_workers=3
    )
    
    # Run pipeline
    try:
        companies = orchestrator.run(
            scrapers=scrapers,
            scraper_configs=scraper_configs,
            enrichers=enrichers if enrichers else None,
            scorer=scorer
        )
        
        if not companies:
            logger.warning("No companies found. Exiting.")
            return
        
        logger.info(f"\nPipeline completed successfully!")
        logger.info(f"Total companies: {len(companies)}")
        
        # Print summary
        if args.enable_scoring:
            high_priority = len([c for c in companies if c.score and c.score.priority == 'high'])
            medium_priority = len([c for c in companies if c.score and c.score.priority == 'medium'])
            low_priority = len([c for c in companies if c.score and c.score.priority == 'low'])
            
            logger.info(f"High priority: {high_priority}")
            logger.info(f"Medium priority: {medium_priority}")
            logger.info(f"Low priority: {low_priority}")
        
        # Export results
        exporter = DataExporter()
        
        formats = [args.output_format] if args.output_format != "all" else ["csv", "json", "excel"]
        
        for fmt in formats:
            filepath = exporter.export(
                companies=companies,
                format=fmt,
                filename=args.output_file
            )
            logger.info(f"Exported to {fmt.upper()}: {filepath}")
        
        # Print top 5 companies
        logger.info("\n" + "=" * 70)
        logger.info("Top 5 Companies:")
        logger.info("=" * 70)
        
        for i, company in enumerate(companies[:5], 1):
            score_str = f"{company.score.total_score:.1f}" if company.score else "N/A"
            priority_str = company.score.priority.upper() if company.score else "N/A"
            
            logger.info(f"\n{i}. {company.name}")
            logger.info(f"   Domain: {company.domain or 'N/A'}")
            logger.info(f"   Source: {company.source.value}")
            logger.info(f"   Score: {score_str} ({priority_str})")
            
            if company.enrichment:
                if company.enrichment.hiring_intent and company.enrichment.hiring_intent.is_hiring:
                    logger.info(f"   Open Positions: {company.enrichment.hiring_intent.total_open_positions}")
                
                if company.enrichment.tech_stack:
                    techs = company.enrichment.tech_stack.all_technologies()[:5]
                    if techs:
                        logger.info(f"   Technologies: {', '.join(techs)}")
        
        logger.info("\n" + "=" * 70)
        logger.info("Pipeline execution completed successfully!")
        logger.info("=" * 70)
    
    except KeyboardInterrupt:
        logger.warning("\nPipeline interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        sys.exit(1)
    
    finally:
        # Cleanup
        for scraper in scrapers:
            if hasattr(scraper, 'close'):
                scraper.close()


if __name__ == "__main__":
    main()
