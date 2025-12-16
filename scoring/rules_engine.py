# OpenLead Intelligence - Rules Engine

"""
Custom logic engine for scoring rules.
Allows defining complex "if this then that" logic for lead prioritization.
"""

from typing import List, Dict, Callable
from models.schemas import Company

class RulesEngine:
    """
    Apply custom business rules to companies.
    """
    
    def __init__(self):
        self.rules: List[Callable[[Company], bool]] = []
        
    def add_rule(self, rule_func: Callable[[Company], bool]):
        self.rules.append(rule_func)
        
    def apply(self, company: Company) -> Dict[str, bool]:
        """Apply all rules and return results."""
        results = {}
        for i, rule in enumerate(self.rules):
            results[f"rule_{i}"] = rule(company)
        return results

# Example Rule
def is_high_value_target(company: Company) -> bool:
    """Example: Tech company hiring > 5 people in the US."""
    if not company.enrichment: 
        return False
        
    is_tech = bool(company.enrichment.tech_stack and company.enrichment.tech_stack.frameworks)
    hiring = company.enrichment.hiring_intent and company.enrichment.hiring_intent.total_open_positions > 5
    
    # Check geo
    geo = company.enrichment.geographic_info
    in_us = geo and geo.country in ['USA', 'US', 'United States']
    
    return is_tech and hiring and in_us
