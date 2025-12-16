# OpenLead Intelligence - Company Deduplication

"""
Deduplicate companies based on domain, name similarity, and other attributes.
"""

from typing import List, Set
from difflib import SequenceMatcher

from models.schemas import Company
from utils.logger import get_logger
from utils.helpers import extract_domain, clean_company_name

logger = get_logger(__name__)


class CompanyDeduplicator:
    """
    Deduplicate companies using multiple strategies.
    
    Strategies:
    1. Exact domain match
    2. Fuzzy company name matching
    3. Website URL matching
    """
    
    def __init__(self, name_similarity_threshold: float = 0.85):
        """
        Initialize deduplicator.
        
        Args:
            name_similarity_threshold: Threshold for fuzzy name matching (0-1)
        """
        self.name_similarity_threshold = name_similarity_threshold
        logger.info(f"Initialized CompanyDeduplicator (threshold={name_similarity_threshold})")
    
    def deduplicate(self, companies: List[Company]) -> List[Company]:
        """
        Deduplicate list of companies.
        
        Args:
            companies: List of companies
        
        Returns:
            Deduplicated list
        """
        if not companies:
            return []
        
        logger.info(f"Deduplicating {len(companies)} companies")
        
        unique_companies = []
        seen_domains: Set[str] = set()
        seen_names: List[str] = []
        
        for company in companies:
            # Extract domain
            domain = None
            if company.domain:
                domain = company.domain.lower()
            elif company.website:
                domain = extract_domain(str(company.website))
            
            # Check domain-based deduplication
            if domain and domain in seen_domains:
                logger.debug(f"Duplicate domain: {domain} ({company.name})")
                continue
            
            # Check name-based deduplication
            clean_name = clean_company_name(company.name).lower()
            is_duplicate = False
            
            for seen_name in seen_names:
                similarity = self._calculate_similarity(clean_name, seen_name)
                if similarity >= self.name_similarity_threshold:
                    logger.debug(
                        f"Duplicate name: {company.name} ~ {seen_name} "
                        f"(similarity: {similarity:.2f})"
                    )
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue
            
            # Add to unique companies
            unique_companies.append(company)
            if domain:
                seen_domains.add(domain)
            seen_names.append(clean_name)
        
        logger.info(
            f"Deduplication complete: {len(unique_companies)}/{len(companies)} unique companies "
            f"({len(companies) - len(unique_companies)} duplicates removed)"
        )
        
        return unique_companies
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings.
        
        Args:
            str1: First string
            str2: Second string
        
        Returns:
            Similarity score (0-1)
        """
        return SequenceMatcher(None, str1, str2).ratio()
    
    def merge_duplicates(self, companies: List[Company]) -> List[Company]:
        """
        Merge duplicate companies instead of removing them.
        Combines data from duplicates into a single record.
        
        Args:
            companies: List of companies
        
        Returns:
            List with merged companies
        """
        # TODO: Implement merging logic
        # For now, just deduplicate
        return self.deduplicate(companies)


if __name__ == "__main__":
    from models.schemas import DataSource
    
    # Test deduplicator
    deduplicator = CompanyDeduplicator()
    
    test_companies = [
        Company(name="Example Inc", domain="example.com", source=DataSource.MANUAL),
        Company(name="Example Inc.", domain="example.com", source=DataSource.MANUAL),
        Company(name="Example Corporation", domain="example.com", source=DataSource.MANUAL),
        Company(name="Different Corp", domain="different.com", source=DataSource.MANUAL),
    ]
    
    unique = deduplicator.deduplicate(test_companies)
    
    print(f"Original: {len(test_companies)} companies")
    print(f"Unique: {len(unique)} companies")
    for company in unique:
        print(f"  - {company.name} ({company.domain})")
