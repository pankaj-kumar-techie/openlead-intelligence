# OpenLead Intelligence - Domain/WHOIS Enrichment

"""
Enrichment module to gather domain-level intelligence.
"""

import socket
from typing import Optional
from urllib.parse import urlparse

from models.schemas import Company, CompanyEnrichment, GeographicInfo
from utils.logger import get_logger
from utils.helpers import extract_domain

logger = get_logger(__name__)


class DomainEnricher:
    """
    Enriches company data using Domain/DNS/WHOIS information.
    """

    def __init__(self):
        logger.info("Initialized DomainEnricher")

    def enrich_company(self, company: Company) -> Company:
        """
        Add domain-level details like IP location (geo approximation).
        """
        domain = company.domain
        if not domain and company.website:
            domain = extract_domain(str(company.website))
        
        if not domain:
            return company

        try:
            # Resolve IP to get rough location (GeoIP would be better in prod)
            ip_address = socket.gethostbyname(domain)
            
            # Create enrichment if missing
            if not company.enrichment:
                company.enrichment = CompanyEnrichment()
            
            if not company.enrichment.geographic_info:
                company.enrichment.geographic_info = GeographicInfo()
            
            # Store IP as placeholder for real GeoIP lookup
            # In a real app, use a MaxMind GeoIP library or API here
            company.extra_data['ip_address'] = ip_address
            
            logger.debug(f"Resolved {domain} to {ip_address}")
            
        except Exception as e:
            logger.warning(f"Domain enrichment failed for {domain}: {e}")

        return company
