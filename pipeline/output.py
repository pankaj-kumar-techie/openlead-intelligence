# OpenLead Intelligence - Output Module

"""
Export data to various formats: CSV, JSON, Excel, Parquet.
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models.schemas import Company
from utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class DataExporter:
    """
    Export company data to various formats.
    
    Supported formats:
    - CSV: Simple tabular format
    - JSON: Nested structure with full data
    - Excel: Multiple sheets with formatting
    - Parquet: Efficient columnar format
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize data exporter.
        
        Args:
            output_dir: Output directory (default from settings)
        """
        self.output_dir = output_dir or settings.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized DataExporter (output_dir={self.output_dir})")
    
    def export(
        self,
        companies: List[Company],
        format: str = "csv",
        filename: Optional[str] = None
    ) -> Path:
        """
        Export companies to specified format.
        
        Args:
            companies: List of companies to export
            format: Output format (csv, json, excel, parquet)
            filename: Custom filename (optional)
        
        Returns:
            Path to exported file
        """
        if not companies:
            logger.warning("No companies to export")
            return None
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"companies_{timestamp}"
        
        # Remove extension if provided
        filename = Path(filename).stem
        
        # Export based on format
        format = format.lower()
        
        if format == "csv":
            return self.export_csv(companies, filename)
        elif format == "json":
            return self.export_json(companies, filename)
        elif format == "excel":
            return self.export_excel(companies, filename)
        elif format == "parquet":
            return self.export_parquet(companies, filename)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_csv(self, companies: List[Company], filename: str) -> Path:
        """Export to CSV format."""
        filepath = self.output_dir / f"{filename}.csv"
        
        logger.info(f"Exporting {len(companies)} companies to CSV: {filepath}")
        
        # Convert to flat dictionaries
        data = [company.to_flat_dict() for company in companies]
        
        # Create DataFrame and export
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"CSV export completed: {filepath}")
        return filepath
    
    def export_json(self, companies: List[Company], filename: str) -> Path:
        """Export to JSON format."""
        filepath = self.output_dir / f"{filename}.json"
        
        logger.info(f"Exporting {len(companies)} companies to JSON: {filepath}")
        
        # Convert to dictionaries
        data = [company.to_dict() for company in companies]
        
        # Write JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON export completed: {filepath}")
        return filepath
    
    def export_excel(self, companies: List[Company], filename: str) -> Path:
        """Export to Excel format with multiple sheets."""
        filepath = self.output_dir / f"{filename}.xlsx"
        
        logger.info(f"Exporting {len(companies)} companies to Excel: {filepath}")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Main sheet with all data
            data = [company.to_flat_dict() for company in companies]
            df_main = pd.DataFrame(data)
            df_main.to_excel(writer, sheet_name='Companies', index=False)
            
            # High priority sheet
            high_priority = [
                c.to_flat_dict() for c in companies
                if c.score and c.score.priority == 'high'
            ]
            if high_priority:
                df_high = pd.DataFrame(high_priority)
                df_high.to_excel(writer, sheet_name='High Priority', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Total Companies',
                    'High Priority',
                    'Medium Priority',
                    'Low Priority',
                    'Currently Hiring',
                    'With Tech Stack Data',
                    'With Funding Data'
                ],
                'Count': [
                    len(companies),
                    len([c for c in companies if c.score and c.score.priority == 'high']),
                    len([c for c in companies if c.score and c.score.priority == 'medium']),
                    len([c for c in companies if c.score and c.score.priority == 'low']),
                    len([c for c in companies if c.enrichment and c.enrichment.hiring_intent and c.enrichment.hiring_intent.is_hiring]),
                    len([c for c in companies if c.enrichment and c.enrichment.tech_stack]),
                    len([c for c in companies if c.enrichment and c.enrichment.funding_info])
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        logger.info(f"Excel export completed: {filepath}")
        return filepath
    
    def export_parquet(self, companies: List[Company], filename: str) -> Path:
        """Export to Parquet format."""
        filepath = self.output_dir / f"{filename}.parquet"
        
        logger.info(f"Exporting {len(companies)} companies to Parquet: {filepath}")
        
        # Convert to flat dictionaries
        data = [company.to_flat_dict() for company in companies]
        
        # Create DataFrame and export
        df = pd.DataFrame(data)
        df.to_parquet(filepath, index=False, engine='pyarrow')
        
        logger.info(f"Parquet export completed: {filepath}")
        return filepath


if __name__ == "__main__":
    from models.schemas import DataSource, CompanySize, CompanyEnrichment, LeadScore
    
    # Test exporter
    exporter = DataExporter()
    
    # Create test companies
    test_companies = [
        Company(
            name="Test Company 1",
            domain="test1.com",
            website="https://test1.com",
            description="A test company",
            source=DataSource.MANUAL,
            enrichment=CompanyEnrichment(
                company_size=CompanySize.SMALL,
                employee_count=30
            ),
            score=LeadScore(
                total_score=75.0,
                priority="high"
            )
        ),
        Company(
            name="Test Company 2",
            domain="test2.com",
            source=DataSource.MANUAL,
            score=LeadScore(
                total_score=45.0,
                priority="medium"
            )
        )
    ]
    
    print("Testing Data Exporter...")
    print(f"Test companies: {len(test_companies)}")
    
    # Export to CSV
    csv_path = exporter.export_csv(test_companies, "test_export")
    print(f"CSV exported to: {csv_path}")
    
    # Export to JSON
    json_path = exporter.export_json(test_companies, "test_export")
    print(f"JSON exported to: {json_path}")
