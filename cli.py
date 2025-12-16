#!/usr/bin/env python3
# OpenLead Intelligence - CLI Wrapper

"""
Command Line Interface for OpenLead Intelligence.
Wraps the main pipeline functionality with Click for better UX.
"""

import click
import sys
from pathlib import Path
from main import main as run_pipeline_main

@click.group()
def cli():
    """OpenLead Intelligence CLI"""
    pass

@cli.command()
@click.option('--sources', '-s', multiple=True, default=['product_hunt'], 
              type=click.Choice(['product_hunt', 'angellist', 'clutch', 'crunchbase', 'all']),
              help='Data sources to scrape')
@click.option('--max-companies', '-m', default=10, help='Max companies per source')
@click.option('--output', '-o', default='leads', help='Output filename')
@click.option('--format', '-f', default='csv', type=click.Choice(['csv', 'json', 'excel']), help='Output format')
def scrape(sources, max_companies, output, format):
    """Run the scraping pipeline."""
    # We can reconstruct the args expectation of main.py or refactor main.py to be importable logic
    # Here we just map to the existing arg structure for simplicity
    
    sys.argv = [
        "main.py",
        "--sources", *sources,
        "--max-companies", str(max_companies),
        "--output-file", output,
        "--output-format", format
    ]
    run_pipeline_main()

if __name__ == '__main__':
    cli()
