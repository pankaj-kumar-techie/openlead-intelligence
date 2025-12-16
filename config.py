# OpenLead Intelligence - B2B Lead Intelligence Framework
# Configuration Module

"""
Centralized configuration management for the scraping framework.
Uses environment variables with sensible defaults.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = "OpenLead Intelligence"
    app_version: str = "1.0.0"
    debug: bool = Field(default=True, description="Enable debug mode")
    
    # Scraping Settings
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Initial retry delay in seconds")
    rate_limit_delay: float = Field(default=2.0, description="Delay between requests in seconds")
    
    # User Agent Settings
    user_agent: Optional[str] = Field(
        default=None,
        description="Custom user agent (if None, will rotate automatically)"
    )
    rotate_user_agents: bool = Field(default=True, description="Enable user agent rotation")
    
    # Browser Automation Settings
    headless_browser: bool = Field(default=True, description="Run browser in headless mode")
    browser_timeout: int = Field(default=60, description="Browser operation timeout")
    
    # API Keys (Optional - for platforms with official APIs)
    crunchbase_api_key: Optional[str] = Field(default=None, description="Crunchbase API key")
    hunter_io_api_key: Optional[str] = Field(default=None, description="Hunter.io API key")
    clearbit_api_key: Optional[str] = Field(default=None, description="Clearbit API key")
    
    # Output Settings
    output_dir: Path = Field(default=Path("output"), description="Output directory for results")
    output_format: str = Field(default="csv", description="Default output format (csv, json, excel)")
    
    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_dir: Path = Field(default=Path("logs"), description="Log directory")
    log_to_file: bool = Field(default=True, description="Enable file logging")
    log_to_console: bool = Field(default=True, description="Enable console logging")
    
    # Data Quality Settings
    min_company_name_length: int = Field(default=2, description="Minimum company name length")
    validate_urls: bool = Field(default=True, description="Validate URLs before scraping")
    deduplicate_results: bool = Field(default=True, description="Remove duplicate companies")
    
    # Scoring Settings
    enable_scoring: bool = Field(default=True, description="Enable lead scoring")
    min_score_threshold: float = Field(default=0.0, description="Minimum score to include in results")
    
    # Geographic Settings
    target_countries: list[str] = Field(
        default_factory=lambda: [],
        description="Target countries (empty = all countries)"
    )
    exclude_countries: list[str] = Field(
        default_factory=lambda: [],
        description="Countries to exclude"
    )
    
    # Compliance Settings
    respect_robots_txt: bool = Field(default=False, description="Respect robots.txt")
    max_pages_per_site: int = Field(default=100, description="Maximum pages to scrape per site")
    
    @validator("output_dir", "log_dir", pre=True)
    def create_directories(cls, v):
        """Ensure directories exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v
    
    @validator("output_format")
    def validate_output_format(cls, v):
        """Validate output format."""
        valid_formats = ["csv", "json", "excel", "parquet"]
        v = v.lower()
        if v not in valid_formats:
            raise ValueError(f"Invalid output format. Must be one of {valid_formats}")
        return v
    
    def get_headers(self) -> dict:
        """Get default HTTP headers."""
        from fake_useragent import UserAgent
        
        if self.user_agent:
            user_agent = self.user_agent
        elif self.rotate_user_agents:
            ua = UserAgent()
            user_agent = ua.random
        else:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }


# Global settings instance
settings = Settings()


# Convenience function to reload settings
def reload_settings() -> Settings:
    """Reload settings from environment."""
    global settings
    settings = Settings()
    return settings


if __name__ == "__main__":
    # Print current configuration
    print("Current Configuration:")
    print("=" * 50)
    for field, value in settings.model_dump().items():
        print(f"{field}: {value}")
