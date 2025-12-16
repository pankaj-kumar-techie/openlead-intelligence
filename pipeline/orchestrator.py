# OpenLead Intelligence - Pipeline Orchestrator

"""
Multi-source data collection orchestrator.
Coordinates scraping, enrichment, scoring, and export.
"""

import time
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from models.schemas import Company, ScrapingResult, DataSource
from utils.logger import get_logger
from config import settings
from pipeline.deduplication import CompanyDeduplicator
from pipeline.output import DataExporter

logger = get_logger(__name__)


class PipelineOrchestrator:
    """
    Orchestrate multi-source scraping and enrichment pipeline.
    
    Workflow:
    1. Scrape from multiple sources (parallel)
    2. Deduplicate companies
    3. Enrich with additional data
    4. Score and prioritize
    5. Validate and export
    """
    
    def __init__(
        self,
        enable_enrichment: bool = True,
        enable_scoring: bool = True,
        enable_deduplication: bool = True,
        max_workers: int = 3
    ):
        """
        Initialize pipeline orchestrator.
        
        Args:
            enable_enrichment: Enable data enrichment
            enable_scoring: Enable lead scoring
            enable_deduplication: Enable deduplication
            max_workers: Maximum parallel workers for scraping
        """
        self.enable_enrichment = enable_enrichment
        self.enable_scoring = enable_scoring
        self.enable_deduplication = enable_deduplication
        self.max_workers = max_workers
        
        logger.info(
            f"Initialized PipelineOrchestrator "
            f"(enrichment={enable_enrichment}, scoring={enable_scoring}, "
            f"dedup={enable_deduplication})"
        )
    
    def run(
        self,
        scrapers: List[Any],
        scraper_configs: Optional[List[Dict[str, Any]]] = None,
        enrichers: Optional[List[Any]] = None,
        scorer: Optional[Any] = None
    ) -> List[Company]:
        """
        Run the complete pipeline.
        
        Args:
            scrapers: List of scraper instances
            scraper_configs: List of config dicts for each scraper
            enrichers: List of enricher instances (optional)
            scorer: Scorer instance (optional)
        
        Returns:
            List of processed companies
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting Pipeline Execution")
        logger.info("=" * 60)
        
        # Step 1: Scrape from all sources
        logger.info(f"Step 1: Scraping from {len(scrapers)} sources")
        all_companies = self._scrape_all_sources(scrapers, scraper_configs or [{}] * len(scrapers))
        logger.info(f"Scraped {len(all_companies)} total companies")
        
        if not all_companies:
            logger.warning("No companies scraped. Exiting pipeline.")
            return []
        
        # Step 2: Deduplicate
        if self.enable_deduplication:
            logger.info("Step 2: Deduplicating companies")
            all_companies = self._deduplicate(all_companies)
            logger.info(f"After deduplication: {len(all_companies)} companies")
        
        # Step 3: Enrich
        if self.enable_enrichment and enrichers:
            logger.info(f"Step 3: Enriching with {len(enrichers)} enrichers")
            all_companies = self._enrich_all(all_companies, enrichers)
            logger.info("Enrichment completed")
        
        # Step 4: Score
        if self.enable_scoring and scorer:
            logger.info("Step 4: Scoring companies")
            all_companies = scorer.score_companies(all_companies)
            logger.info("Scoring completed")
        
        # Step 5: Filter by minimum score
        if self.enable_scoring and settings.min_score_threshold > 0:
            original_count = len(all_companies)
            all_companies = [
                c for c in all_companies
                if c.score and c.score.total_score >= settings.min_score_threshold
            ]
            logger.info(
                f"Filtered by score threshold ({settings.min_score_threshold}): "
                f"{len(all_companies)}/{original_count} companies"
            )
        
        execution_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"Pipeline completed in {execution_time:.2f}s")
        logger.info(f"Final result: {len(all_companies)} companies")
        logger.info("=" * 60)
        
        return all_companies
    
    def _scrape_all_sources(
        self,
        scrapers: List[Any],
        configs: List[Dict[str, Any]]
    ) -> List[Company]:
        """
        Scrape from all sources in parallel.
        
        Args:
            scrapers: List of scraper instances
            configs: List of configuration dicts
        
        Returns:
            Combined list of companies
        """
        all_companies = []
        
        # Use ThreadPoolExecutor for parallel scraping
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit scraping tasks
            future_to_scraper = {
                executor.submit(scraper.scrape, **config): scraper
                for scraper, config in zip(scrapers, configs)
            }
            
            # Collect results with progress bar
            with tqdm(total=len(scrapers), desc="Scraping sources") as pbar:
                for future in as_completed(future_to_scraper):
                    scraper = future_to_scraper[future]
                    try:
                        result: ScrapingResult = future.result()
                        
                        if result.success:
                            all_companies.extend(result.companies)
                            logger.info(
                                f"{scraper.__class__.__name__}: "
                                f"{result.total_scraped} companies in {result.execution_time:.2f}s"
                            )
                        else:
                            logger.error(
                                f"{scraper.__class__.__name__} failed: {result.errors}"
                            )
                    
                    except Exception as e:
                        logger.exception(
                            f"Error scraping with {scraper.__class__.__name__}: {e}"
                        )
                    
                    pbar.update(1)
        
        return all_companies
    
    def _deduplicate(self, companies: List[Company]) -> List[Company]:
        """
        Deduplicate companies based on domain and name.
        
        Args:
            companies: List of companies
        
        Returns:
            Deduplicated list
        """
        from pipeline.deduplication import CompanyDeduplicator
        
        deduplicator = CompanyDeduplicator()
        return deduplicator.deduplicate(companies)
    
    def _enrich_all(
        self,
        companies: List[Company],
        enrichers: List[Any]
    ) -> List[Company]:
        """
        Enrich all companies with all enrichers.
        
        Args:
            companies: List of companies
            enrichers: List of enricher instances
        
        Returns:
            Enriched companies
        """
        with tqdm(total=len(companies) * len(enrichers), desc="Enriching companies") as pbar:
            for enricher in enrichers:
                logger.info(f"Enriching with {enricher.__class__.__name__}")
                
                for company in companies:
                    try:
                        enricher.enrich_company(company)
                    except Exception as e:
                        logger.error(
                            f"Error enriching {company.name} with "
                            f"{enricher.__class__.__name__}: {e}"
                        )
                    pbar.update(1)
        
        return companies


if __name__ == "__main__":
    print("Pipeline Orchestrator")
    print("\nExample usage:")
    print("  orchestrator = PipelineOrchestrator()")
    print("  companies = orchestrator.run(")
    print("      scrapers=[scraper1, scraper2],")
    print("      enrichers=[enricher1, enricher2],")
    print("      scorer=scorer")
    print("  )")
