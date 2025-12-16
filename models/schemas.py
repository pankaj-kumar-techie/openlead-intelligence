# OpenLead Intelligence - Data Schemas

"""
Pydantic models for data validation and serialization.
Defines schemas for companies, leads, enrichment data, and scoring.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator, field_validator


class CompanySize(str, Enum):
    """Company size categories."""
    STARTUP = "startup"  # 1-10 employees
    SMALL = "small"  # 11-50 employees
    MEDIUM = "medium"  # 51-200 employees
    LARGE = "large"  # 201-1000 employees
    ENTERPRISE = "enterprise"  # 1000+ employees
    UNKNOWN = "unknown"


class FundingStage(str, Enum):
    """Funding stage categories."""
    BOOTSTRAPPED = "bootstrapped"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D_PLUS = "series_d_plus"
    IPO = "ipo"
    ACQUIRED = "acquired"
    UNKNOWN = "unknown"


class DataSource(str, Enum):
    """Data source types."""
    PRODUCT_HUNT = "product_hunt"
    ANGELLIST = "angellist"
    CRUNCHBASE = "crunchbase"
    CLUTCH = "clutch"
    JOB_BOARDS = "job_boards"
    LINKEDIN = "linkedin"
    MANUAL = "manual"
    API = "api"
    OTHER = "other"


class TechStack(BaseModel):
    """Technology stack information."""
    languages: List[str] = Field(default_factory=list, description="Programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks and libraries")
    databases: List[str] = Field(default_factory=list, description="Database systems")
    cloud_providers: List[str] = Field(default_factory=list, description="Cloud platforms")
    tools: List[str] = Field(default_factory=list, description="Development tools")
    analytics: List[str] = Field(default_factory=list, description="Analytics tools")
    marketing: List[str] = Field(default_factory=list, description="Marketing tools")
    
    def all_technologies(self) -> List[str]:
        """Get all technologies as a flat list."""
        return (
            self.languages + self.frameworks + self.databases +
            self.cloud_providers + self.tools + self.analytics + self.marketing
        )


class HiringIntent(BaseModel):
    """Hiring intent signals."""
    total_open_positions: int = Field(default=0, description="Total open positions")
    recent_postings: int = Field(default=0, description="Postings in last 30 days")
    engineering_positions: int = Field(default=0, description="Engineering roles")
    sales_positions: int = Field(default=0, description="Sales roles")
    marketing_positions: int = Field(default=0, description="Marketing roles")
    hiring_velocity: float = Field(default=0.0, description="Hiring rate (jobs/month)")
    is_hiring: bool = Field(default=False, description="Currently hiring")
    
    @field_validator("hiring_velocity")
    @classmethod
    def round_velocity(cls, v):
        """Round hiring velocity to 2 decimal places."""
        return round(v, 2)


class FundingInfo(BaseModel):
    """Funding information."""
    stage: FundingStage = Field(default=FundingStage.UNKNOWN)
    total_funding: Optional[float] = Field(default=None, description="Total funding in USD")
    last_funding_date: Optional[datetime] = None
    last_funding_amount: Optional[float] = None
    investors: List[str] = Field(default_factory=list)
    valuation: Optional[float] = Field(default=None, description="Company valuation in USD")


class GeographicInfo(BaseModel):
    """Geographic information."""
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    headquarters: Optional[str] = None


class SocialProfiles(BaseModel):
    """Social media profiles."""
    linkedin: Optional[HttpUrl] = None
    twitter: Optional[HttpUrl] = None
    facebook: Optional[HttpUrl] = None
    github: Optional[HttpUrl] = None
    crunchbase: Optional[HttpUrl] = None


class CompanyEnrichment(BaseModel):
    """Enriched company data."""
    tech_stack: Optional[TechStack] = None
    hiring_intent: Optional[HiringIntent] = None
    funding_info: Optional[FundingInfo] = None
    geographic_info: Optional[GeographicInfo] = None
    social_profiles: Optional[SocialProfiles] = None
    employee_count: Optional[int] = None
    company_size: CompanySize = CompanySize.UNKNOWN
    founded_year: Optional[int] = None
    industry: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    @field_validator("founded_year")
    @classmethod
    def validate_year(cls, v):
        """Validate founded year."""
        if v is not None:
            current_year = datetime.now().year
            if v < 1800 or v > current_year:
                raise ValueError(f"Invalid year: {v}")
        return v


class LeadScore(BaseModel):
    """Lead scoring information."""
    total_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Total score (0-100)")
    intent_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Intent score")
    fit_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Fit score")
    engagement_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Engagement score")
    priority: str = Field(default="low", description="Priority level (low, medium, high)")
    
    @field_validator("total_score", "intent_score", "fit_score", "engagement_score")
    @classmethod
    def round_scores(cls, v):
        """Round scores to 2 decimal places."""
        return round(v, 2)
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """Validate priority level."""
        valid_priorities = ["low", "medium", "high"]
        if v.lower() not in valid_priorities:
            raise ValueError(f"Invalid priority. Must be one of {valid_priorities}")
        return v.lower()


class Company(BaseModel):
    """Core company data model."""
    # Basic Information
    name: str = Field(..., min_length=1, description="Company name")
    domain: Optional[str] = Field(default=None, description="Company domain")
    website: Optional[HttpUrl] = None
    description: Optional[str] = None
    
    # Source Information
    source: DataSource = Field(default=DataSource.OTHER)
    source_url: Optional[HttpUrl] = None
    
    # Enrichment
    enrichment: Optional[CompanyEnrichment] = None
    
    # Scoring
    score: Optional[LeadScore] = None
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Additional data
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("name")
    @classmethod
    def clean_name(cls, v):
        """Clean company name."""
        return v.strip()
    
    def to_dict(self) -> dict:
        """Convert to dictionary with datetime serialization."""
        data = self.model_dump()
        # Convert datetime to ISO format
        data['scraped_at'] = self.scraped_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    def to_flat_dict(self) -> dict:
        """Convert to flat dictionary for CSV export."""
        flat = {
            "company_name": self.name,
            "domain": self.domain,
            "website": str(self.website) if self.website else None,
            "description": self.description,
            "source": self.source.value,
            "source_url": str(self.source_url) if self.source_url else None,
            "scraped_at": self.scraped_at.isoformat(),
        }
        
        # Add enrichment data
        if self.enrichment:
            flat["employee_count"] = self.enrichment.employee_count
            flat["company_size"] = self.enrichment.company_size.value
            flat["founded_year"] = self.enrichment.founded_year
            flat["industry"] = self.enrichment.industry
            
            if self.enrichment.geographic_info:
                flat["country"] = self.enrichment.geographic_info.country
                flat["city"] = self.enrichment.geographic_info.city
            
            if self.enrichment.funding_info:
                flat["funding_stage"] = self.enrichment.funding_info.stage.value
                flat["total_funding"] = self.enrichment.funding_info.total_funding
            
            if self.enrichment.hiring_intent:
                flat["open_positions"] = self.enrichment.hiring_intent.total_open_positions
                flat["is_hiring"] = self.enrichment.hiring_intent.is_hiring
            
            if self.enrichment.tech_stack:
                flat["technologies"] = ", ".join(self.enrichment.tech_stack.all_technologies()[:10])
        
        # Add scoring data
        if self.score:
            flat["total_score"] = self.score.total_score
            flat["priority"] = self.score.priority
        
        return flat


class ScrapingResult(BaseModel):
    """Result of a scraping operation."""
    success: bool = True
    companies: List[Company] = Field(default_factory=list)
    total_scraped: int = 0
    total_enriched: int = 0
    total_scored: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_time: float = 0.0
    source: DataSource = DataSource.OTHER
    
    def add_company(self, company: Company):
        """Add a company to results."""
        self.companies.append(company)
        self.total_scraped += 1
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)


if __name__ == "__main__":
    # Test schemas
    company = Company(
        name="Example Inc.",
        domain="example.com",
        website="https://example.com",
        description="A test company",
        source=DataSource.PRODUCT_HUNT,
        enrichment=CompanyEnrichment(
            company_size=CompanySize.STARTUP,
            employee_count=25,
            tech_stack=TechStack(
                languages=["Python", "JavaScript"],
                frameworks=["Django", "React"]
            ),
            hiring_intent=HiringIntent(
                total_open_positions=5,
                is_hiring=True
            )
        ),
        score=LeadScore(
            total_score=75.5,
            priority="high"
        )
    )
    
    print("Company Model:")
    print(company.model_dump_json(indent=2))
    
    print("\nFlat Dictionary:")
    print(company.to_flat_dict())
