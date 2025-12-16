# OpenLead Intelligence - Lead Scoring Engine

"""
Configurable lead scoring engine for prioritizing companies.
Scores based on multiple factors: hiring intent, tech stack, funding, size, etc.
"""

from typing import Optional, Dict, List
from models.schemas import Company, LeadScore, CompanySize, FundingStage
from utils.logger import get_logger

logger = get_logger(__name__)


class LeadScorer:
    """
    Lead scoring engine with configurable weights.
    
    Calculates scores based on:
    - Hiring intent (job postings, growth signals)
    - Company fit (size, industry, location)
    - Technology stack (relevant technologies)
    - Funding and growth (recent funding, employee growth)
    - Engagement signals (website activity, social presence)
    """
    
    # Default scoring weights (0-1, must sum to 1.0)
    DEFAULT_WEIGHTS = {
        'intent': 0.35,      # Hiring intent and growth signals
        'fit': 0.30,         # Company size, industry, location fit
        'tech': 0.20,        # Technology stack relevance
        'engagement': 0.15,  # Social presence and activity
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize lead scorer.
        
        Args:
            weights: Custom scoring weights (optional)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        
        # Validate weights
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total}, normalizing to 1.0")
            self.weights = {k: v/total for k, v in self.weights.items()}
        
        logger.info(f"Initialized LeadScorer with weights: {self.weights}")
    
    def score(self, company: Company) -> LeadScore:
        """
        Calculate lead score for a company.
        
        Args:
            company: Company to score
        
        Returns:
            LeadScore object
        """
        # Calculate component scores
        intent_score = self._calculate_intent_score(company)
        fit_score = self._calculate_fit_score(company)
        tech_score = self._calculate_tech_score(company)
        engagement_score = self._calculate_engagement_score(company)
        
        # Calculate weighted total score
        total_score = (
            intent_score * self.weights['intent'] +
            fit_score * self.weights['fit'] +
            tech_score * self.weights['tech'] +
            engagement_score * self.weights['engagement']
        )
        
        # Determine priority
        priority = self._determine_priority(total_score)
        
        lead_score = LeadScore(
            total_score=total_score,
            intent_score=intent_score,
            fit_score=fit_score,
            engagement_score=engagement_score,
            priority=priority
        )
        
        logger.debug(f"Scored {company.name}: {total_score:.2f} ({priority})")
        
        return lead_score
    
    def _calculate_intent_score(self, company: Company) -> float:
        """Calculate intent score based on hiring signals."""
        score = 0.0
        
        if not company.enrichment or not company.enrichment.hiring_intent:
            return score
        
        hiring = company.enrichment.hiring_intent
        
        # Active hiring
        if hiring.is_hiring:
            score += 30.0
        
        # Number of open positions
        if hiring.total_open_positions > 0:
            score += min(hiring.total_open_positions * 5, 30.0)
        
        # Recent postings (last 30 days)
        if hiring.recent_postings > 0:
            score += min(hiring.recent_postings * 10, 20.0)
        
        # Hiring velocity
        if hiring.hiring_velocity > 0:
            score += min(hiring.hiring_velocity * 5, 20.0)
        
        return min(score, 100.0)
    
    def _calculate_fit_score(self, company: Company) -> float:
        """Calculate fit score based on company characteristics."""
        score = 50.0  # Base score
        
        if not company.enrichment:
            return score
        
        enrichment = company.enrichment
        
        # Company size (prefer growing startups and scale-ups)
        size_scores = {
            CompanySize.STARTUP: 70.0,
            CompanySize.SMALL: 80.0,
            CompanySize.MEDIUM: 90.0,
            CompanySize.LARGE: 70.0,
            CompanySize.ENTERPRISE: 50.0,
            CompanySize.UNKNOWN: 40.0,
        }
        score = size_scores.get(enrichment.company_size, 50.0)
        
        # Funding stage (prefer funded companies)
        if enrichment.funding_info:
            funding_scores = {
                FundingStage.SEED: 60.0,
                FundingStage.SERIES_A: 80.0,
                FundingStage.SERIES_B: 90.0,
                FundingStage.SERIES_C: 85.0,
                FundingStage.SERIES_D_PLUS: 75.0,
            }
            funding_score = funding_scores.get(enrichment.funding_info.stage, 0)
            score = (score + funding_score) / 2
        
        # Employee count (prefer 20-500 employees)
        if enrichment.employee_count:
            if 20 <= enrichment.employee_count <= 500:
                score += 10.0
            elif enrichment.employee_count < 20:
                score += 5.0
        
        return min(score, 100.0)
    
    def _calculate_tech_score(self, company: Company) -> float:
        """Calculate tech score based on technology stack."""
        score = 0.0
        
        if not company.enrichment or not company.enrichment.tech_stack:
            return score
        
        tech_stack = company.enrichment.tech_stack
        all_techs = tech_stack.all_technologies()
        
        # Base score for having tech stack data
        if all_techs:
            score = 40.0
        
        # Modern frameworks (React, Vue, Angular, etc.)
        modern_frameworks = ['React', 'Vue', 'Angular', 'Svelte', 'Next.js']
        if any(tech in str(tech_stack.frameworks) for tech in modern_frameworks):
            score += 20.0
        
        # Cloud infrastructure
        if tech_stack.cloud_providers:
            score += 15.0
        
        # Modern databases
        modern_dbs = ['MongoDB', 'PostgreSQL', 'Redis']
        if any(db in str(tech_stack.databases) for db in modern_dbs):
            score += 15.0
        
        # Analytics tools (shows data-driven culture)
        if tech_stack.analytics:
            score += 10.0
        
        return min(score, 100.0)
    
    def _calculate_engagement_score(self, company: Company) -> float:
        """Calculate engagement score based on online presence."""
        score = 0.0
        
        # Has website
        if company.website or company.domain:
            score += 30.0
        
        # Has description
        if company.description:
            score += 20.0
        
        if not company.enrichment:
            return score
        
        # Social profiles
        if company.enrichment.social_profiles:
            profiles = company.enrichment.social_profiles
            if profiles.linkedin:
                score += 15.0
            if profiles.twitter:
                score += 10.0
            if profiles.github:
                score += 15.0
            if profiles.crunchbase:
                score += 10.0
        
        return min(score, 100.0)
    
    def _determine_priority(self, score: float) -> str:
        """
        Determine priority level based on score.
        
        Args:
            score: Total score (0-100)
        
        Returns:
            Priority level: 'low', 'medium', or 'high'
        """
        if score >= 70:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def score_companies(self, companies: List[Company]) -> List[Company]:
        """
        Score multiple companies and add scores to their objects.
        
        Args:
            companies: List of companies to score
        
        Returns:
            List of companies with scores
        """
        logger.info(f"Scoring {len(companies)} companies")
        
        for company in companies:
            company.score = self.score(company)
        
        # Sort by score (highest first)
        companies.sort(key=lambda c: c.score.total_score if c.score else 0, reverse=True)
        
        logger.info("Scoring completed")
        return companies


if __name__ == "__main__":
    from models.schemas import (
        Company, CompanyEnrichment, HiringIntent,
        TechStack, DataSource, CompanySize
    )
    
    # Test scorer
    scorer = LeadScorer()
    
    # Example company
    test_company = Company(
        name="Test Startup Inc",
        website="https://example.com",
        description="An innovative tech startup",
        source=DataSource.MANUAL,
        enrichment=CompanyEnrichment(
            company_size=CompanySize.SMALL,
            employee_count=45,
            hiring_intent=HiringIntent(
                total_open_positions=8,
                is_hiring=True,
                recent_postings=5
            ),
            tech_stack=TechStack(
                frameworks=["React", "Django"],
                databases=["PostgreSQL"],
                cloud_providers=["AWS"]
            )
        )
    )
    
    score = scorer.score(test_company)
    
    print("Lead Scoring Example:")
    print(f"Company: {test_company.name}")
    print(f"Total Score: {score.total_score:.2f}")
    print(f"Intent Score: {score.intent_score:.2f}")
    print(f"Fit Score: {score.fit_score:.2f}")
    print(f"Tech Score: {score.tech_score:.2f}")
    print(f"Engagement Score: {score.engagement_score:.2f}")
    print(f"Priority: {score.priority.upper()}")
