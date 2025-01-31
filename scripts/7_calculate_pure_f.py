import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from tqdm import tqdm

class PureFCalculator:
    """
    A class to calculate Pure F scores from citation matching summaries by year.
    
    Pure F Score is a metric that measures the quality of citation matching:
    - Calculated as (matched_citations / total_forward_citations)
    - Ranges from 0 (no matches) to 1 (perfect matching)
    
    This class:
    1. Loads citation matching summaries from flag_summary.json
    2. Calculates Pure F scores for each year
    3. Adds quality metrics and validation
    4. Saves results to pure_f_summary.json
    
    Attributes:
        logger: Logging instance for tracking process and errors
        schema: Configuration schema loaded from JSON
        base_path: Base directory path for data files
    """
    
    def __init__(self, schema_path: Path):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/pure_f_calculation.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load schema
        with open(schema_path) as f:
            self.schema = json.load(f)
        
        self.base_path = Path(self.schema['config']['base_path'])
        
    def calculate_company_pure_f(self, company: str) -> Optional[Dict]:
        """
        Calculate Pure F scores for a company's patents by year.
        
        Args:
            company (str): Name of the company to process
            
        Returns:
            Optional[Dict]: Dictionary containing yearly Pure F scores and metrics, or None if processing fails
            
        The function:
        1. Loads citation matching summary from flag_summary.json
        2. Validates data structure and required fields
        3. Calculates Pure F scores for each year
        4. Saves results to pure_f_summary.json
        
        Example output structure:
        {
            "2020": {
                "company_name": "company_x",
                "year": 2020,
                "total_citations": 500,
                "matched_citations": 450,
                "pure_f_score": 0.90,
                "quality_metrics": {
                    "match_rate": 90.0,
                    "perfect_matches": 40,
                    "no_matches": 2
                },
                "total_patents": 50,
                "processing_date": "2025-01-30"
            },
            "2021": {
                ...
            }
        }
        """
        try:
            # Load flag summary data
            flag_file = self.base_path / company / "flag_summary.json"
            if not flag_file.exists():
                self.logger.error(f"Flag summary file not found for {company}")
                return None
                
            with open(flag_file) as f:
                flag_data = json.load(f)
            
            # Debug print the structure for the first company
            if company == list(self.schema['config']['companies'])[0]:
                self.logger.info(f"Example data structure for {company}:")
                self.logger.info(json.dumps(flag_data, indent=2))
            
            # Check if flag_data is properly structured
            if not isinstance(flag_data, dict):
                self.logger.error(f"Flag data is not a dictionary for {company}")
                return None
                
            yearly_results = {}
            for year, year_data in flag_data.items():
                # Add more detailed debugging
                self.logger.debug(f"Processing year {year} for {company}")
                self.logger.debug(f"Year data structure: {year_data}")
                
                # Validate year_data structure
                if not isinstance(year_data, dict):
                    self.logger.error(f"Invalid year data structure for {company}, year {year}")
                    continue
                    
                # Check for required fields with detailed logging
                required_fields = ['total_forward_citations', 'matched_citations']
                missing_fields = [field for field in required_fields if field not in year_data]
                if missing_fields:
                    self.logger.error(f"Missing fields {missing_fields} for {company}, year {year}")
                    continue
                
                year_pure_f = self._calculate_year_pure_f(year_data, company, int(year))
                if year_pure_f:
                    yearly_results[year] = year_pure_f
            
            if not yearly_results:
                self.logger.error(f"No valid Pure F results calculated for {company}")
                return None
            
            # Save results
            output_file = self.base_path / company / "pure_f_summary.json"
            with open(output_file, 'w') as f:
                json.dump(yearly_results, f, indent=2)
            
            return yearly_results
            
        except Exception as e:
            self.logger.error(f"Error calculating Pure F for {company}: {str(e)}")
            return None
            
    def _calculate_year_pure_f(self, flag_data: Dict, company: str, year: int) -> Optional[Dict]:
        """
        Calculate Pure F metrics for a specific year's patent data.
        
        Args:
            flag_data (Dict): Citation matching data for the year
                Required fields:
                - total_forward_citations
                - matched_citations
                - average_match_rate
                - patents_with_perfect_match
                - patents_with_no_match
                - total_patents
            company (str): Name of the company
            year (int): Year being processed
            
        Returns:
            Optional[Dict]: Dictionary containing Pure F score and related metrics,
                          or None if calculation fails
        
        The function:
        1. Validates required input data
        2. Checks for valid citation counts
        3. Calculates Pure F score (matched_citations / total_citations)
        4. Adds quality metrics and metadata
        
        Pure F Score interpretation:
        - 1.0: Perfect citation matching
        - 0.0: No successful matches
        - Values in between represent partial matching success
        
        Note:
        - Returns None for years with zero citations
        - Validates data types to ensure accurate calculations
        """
        try:
            # Validate inputs
            if not all(k in flag_data for k in ['total_forward_citations', 'matched_citations']):
                self.logger.error(f"Missing required data for {company}, year {year}")
                return None
                
            total_citations = flag_data['total_forward_citations']
            matched_citations = flag_data['matched_citations']
            
            # Validate citation counts
            if not isinstance(total_citations, (int, float)) or not isinstance(matched_citations, (int, float)):
                self.logger.error(f"Invalid citation data types for {company}, year {year}")
                return None
                
            if total_citations == 0:
                self.logger.warning(f"No citations for {company} in year {year}")
                return None
            
            pure_f_score = matched_citations / total_citations
            
            return {
                'company_name': company,
                'year': year,
                'total_citations': total_citations,
                'matched_citations': matched_citations,
                'pure_f_score': float(pure_f_score),
                'quality_metrics': {
                    'match_rate': float(flag_data['average_match_rate']),
                    'perfect_matches': flag_data['patents_with_perfect_match'],
                    'no_matches': flag_data['patents_with_no_match']
                },
                'total_patents': flag_data['total_patents'],
                'processing_date': datetime.now().strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating year {year} Pure F for {company}: {str(e)}")
            return None

def main():
    """
    Main execution function for Pure F score calculation.
    
    The function:
    1. Loads configuration from workflow_schema_cleaned.json
    2. Initializes PureFCalculator instance
    3. Processes each company in the configuration
    4. Tracks success/failure statistics
    5. Prints processing summary
    
    Required files:
    - workflow_schema_cleaned.json
    - Data/company_name/flag_summary.json (for each company)
    
    Outputs:
    - Data/company_name/pure_f_summary.json (for each company)
    - logs/pure_f_calculation.log
    
    The Pure F calculation process:
    1. Loads citation matching summaries
    2. Validates data completeness
    3. Calculates Pure F scores by year
    4. Adds quality metrics
    5. Saves results with proper formatting
    
    Note:
    - Companies with no valid citation data will be marked as failed
    - Years with zero citations will be skipped
    - Data validation ensures accurate Pure F calculations
    """
    # Load schema
    schema_path = Path('workflow_schema_cleaned.json')
    if not schema_path.exists():
        raise FileNotFoundError("Cleaned schema file not found")
        
    # Initialize calculator
    calculator = PureFCalculator(schema_path)
    
    # Process each company
    companies = calculator.schema['config']['companies']
    
    # Setup progress tracking
    pbar = tqdm(companies, desc="Processing Companies", unit="company")
    stats = {'successful': [], 'failed': []}
    
    for company in pbar:
        pbar.set_description(f"Processing {company}")
        
        try:
            results = calculator.calculate_company_pure_f(company)
            
            if results is not None:
                stats['successful'].append(company)
                pbar.set_postfix(status="Success")
            else:
                stats['failed'].append(company)
                pbar.set_postfix(status="Failed")
                
        except Exception as e:
            calculator.logger.error(f"Failed to process {company}: {str(e)}")
            stats['failed'].append(company)
            pbar.set_postfix(status="Error")
            continue
    
    # Print summary
    print("\nPure F Calculation Summary")
    print("=" * 50)
    print(f"Successfully processed: {len(stats['successful'])} companies")
    print(f"Failed to process: {len(stats['failed'])} companies")
    
    if stats['failed']:
        print("\nFailed companies:")
        for company in stats['failed']:
            print(f"- {company}")

if __name__ == "__main__":
    main()
