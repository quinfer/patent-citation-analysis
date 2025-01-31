import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from tqdm import tqdm

class DisruptionIndexCalculator:
    """
    Calculate Disruption Index (DI) from Pure F scores and citation metrics.
    
    The Disruption Index measures a company's technological impact and innovation:
    DI = Pure F Score × Quality Factor × Impact Factor
    
    Components:
    1. Pure F Score (0-1): Measures citation matching quality
    2. Quality Factor (0-1): Weighted score of match quality distribution
    3. Impact Factor (0-1): Logarithmic scale of citations per patent
    
    Attributes:
        logger: Logging instance for tracking process and errors
        schema: Configuration schema loaded from JSON
        base_path: Base directory path for data files
    """
    
    def __init__(self, schema_path: Path):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/disruption_index.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load schema
        with open(schema_path) as f:
            self.schema = json.load(f)
        
        self.base_path = Path(self.schema['config']['base_path'])
        
    def calculate_company_di(self, company: str) -> Optional[Dict]:
        """
        Calculate Disruption Index for a company using Pure F scores and citation data.
        
        Args:
            company (str): Name of the company to process
            
        Returns:
            Optional[Dict]: Dictionary containing DI scores and components, or None if processing fails
            
        The function:
        1. Loads Pure F scores from pure_f_summary.json
        2. Calculates quality and impact factors
        3. Combines factors to compute final DI
        4. Saves results to di_summary.json
        
        Example output structure:
        {
            "company_name": "company_x",
            "disruption_index": 0.65,
            "components": {
                "pure_f_score": 0.90,
                "quality_factor": 0.80,
                "impact_factor": 0.90
            },
            "metrics": {
                "total_patents": 100,
                "total_citations": 1000,
                "citations_per_patent": 10.0,
                "matched_citations_per_patent": 9.0
            },
            "quality_distribution": {
                "high_quality_matches": 80,
                "medium_quality_matches": 15,
                "low_quality_matches": 5,
                "poor_quality_matches": 0
            },
            "processing_date": "2025-01-30"
        }
        """
        try:
            # Load Pure F summary
            pure_f_file = self.base_path / company / "pure_f_summary.json"
            if not pure_f_file.exists():
                self.logger.error(f"Pure F summary file not found for {company}")
                return None
                
            with open(pure_f_file) as f:
                pure_f_data = json.load(f)
            
            # Calculate DI
            di_results = self._calculate_di(pure_f_data, company)
            
            # Save results
            output_file = self.base_path / company / "di_summary.json"
            with open(output_file, 'w') as f:
                json.dump(di_results, f, indent=2)
            
            self.logger.info(f"Saved DI results for {company}")
            return di_results
            
        except Exception as e:
            self.logger.error(f"Error calculating DI for {company}: {str(e)}")
            return None
            
    def _calculate_di(self, pure_f_data: Dict, company: str) -> Dict:
        """
        Calculate Disruption Index components and final score.
        
        Args:
            pure_f_data (Dict): Pure F scores and citation metrics by year
                Format: {
                    "2020": {
                        "total_citations": 100,
                        "matched_citations": 90,
                        "pure_f_score": 0.9,
                        "quality_metrics": {
                            "match_rate": 0.9,
                            "perfect_matches": 80,
                            "no_matches": 5
                        },
                        "total_patents": 100,
                        ...
                    },
                    "2021": { ... }
                }
            company (str): Company name
            
        Returns:
            Dict: Disruption Index results with all components
        """
        try:
            yearly_results = {}
            
            for year, year_data in pure_f_data.items():
                # Get values from the correct fields
                total_citations = year_data['total_citations']
                matched_citations = year_data['matched_citations']
                total_patents = year_data['total_patents']
                pure_f = year_data['pure_f_score']
                
                # Calculate citations per patent metrics
                citations_per_patent = total_citations / total_patents if total_patents > 0 else 0.0
                matched_citations_per_patent = matched_citations / total_patents if total_patents > 0 else 0.0
                
                # Calculate quality metrics
                quality_metrics = {
                    'high_quality_matches': year_data['quality_metrics']['perfect_matches'],
                    'medium_quality_matches': (total_patents - 
                        year_data['quality_metrics']['perfect_matches'] - 
                        year_data['quality_metrics']['no_matches']),
                    'low_quality_matches': year_data['quality_metrics']['no_matches'],
                    'poor_quality_matches': 0
                }
                
                # Calculate DI components
                quality_factor = self._calculate_quality_factor(quality_metrics)
                impact_factor = self._calculate_impact_factor(citations_per_patent)
                
                # Calculate final DI
                disruption_index = pure_f * quality_factor * impact_factor
                
                yearly_results[year] = {
                    'disruption_index': float(disruption_index),
                    'components': {
                        'pure_f_score': float(pure_f),
                        'quality_factor': float(quality_factor),
                        'impact_factor': float(impact_factor)
                    },
                    'metrics': {
                        'total_patents': total_patents,
                        'total_citations': total_citations,
                        'citations_per_patent': float(citations_per_patent),
                        'matched_citations_per_patent': float(matched_citations_per_patent)
                    },
                    'quality_distribution': quality_metrics,
                    'processing_date': year_data['processing_date']
                }
            
            # Aggregate company-level results
            results = {
                'company_name': company,
                'yearly_di': yearly_results,
                'processing_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in DI calculation: {str(e)}")
            raise
            
    def _calculate_quality_factor(self, quality_metrics: Dict) -> float:
        """
        Calculate quality factor based on match quality distribution.
        
        Args:
            quality_metrics (Dict): Distribution of match quality levels
                Keys: high_quality_matches, medium_quality_matches, 
                     low_quality_matches, poor_quality_matches
                
        Returns:
            float: Weighted quality factor (0-1)
            
        Weights:
        - High quality matches: 1.0
        - Medium quality matches: 0.7
        - Low quality matches: 0.4
        - Poor quality matches: 0.1
        
        The quality factor rewards companies with higher proportions
        of high-quality citation matches.
        """
        weights = {
            'high_quality_matches': 1.0,
            'medium_quality_matches': 0.7,
            'low_quality_matches': 0.4,
            'poor_quality_matches': 0.1
        }
        
        total_matches = sum(quality_metrics.values())
        if total_matches == 0:
            return 0.0
            
        weighted_sum = sum(weights[k] * v for k, v in quality_metrics.items())
        return weighted_sum / total_matches
        
    def _calculate_impact_factor(self, citations_per_patent: float) -> float:
        """
        Calculate impact factor based on citations per patent.
        
        Args:
            citations_per_patent (float): Average citations per patent
            
        Returns:
            float: Impact factor (0-1)
            
        Formula: min(1.0, 0.1 * (1 + ln(citations_per_patent)))
        
        The logarithmic scale:
        - Dampens the effect of extremely high citation counts
        - Provides meaningful differentiation for typical citation ranges
        - Returns 0 for patents with no citations
        """
        # Using a logarithmic scale to dampen the effect of high citation counts
        if citations_per_patent <= 0:
            return 0.0
        return min(1.0, 0.1 * (1 + np.log(citations_per_patent)))

    def create_panel_dataset(self, stats: Dict[str, List[str]]) -> None:
        """
        Create a panel dataset of Disruption Index scores for all successfully processed companies.
        
        Args:
            stats (Dict[str, List[str]]): Dictionary containing lists of successful and failed companies
        
        Creates a CSV file with format:
        company_name, year, disruption_index, pure_f_score, quality_factor, impact_factor, 
        total_patents, total_citations, citations_per_patent, matched_citations_per_patent
        
        Example:
        company_name,year,disruption_index,pure_f_score,quality_factor,impact_factor,...
        apple,2020,0.65,0.90,0.80,0.90,100,1000,10.0,9.0
        apple,2021,0.70,0.92,0.85,0.89,120,1200,10.0,9.2
        boeing,2020,0.55,0.80,0.75,0.92,80,800,10.0,8.0
        ...
        """
        try:
            panel_data = []
            
            # Process each successful company
            for company in stats['successful']:
                di_file = self.base_path / company / "di_summary.json"
                
                if not di_file.exists():
                    self.logger.warning(f"DI summary file not found for {company}")
                    continue
                    
                with open(di_file) as f:
                    di_data = json.load(f)
                
                # Extract yearly data
                for year, year_data in di_data['yearly_di'].items():
                    row = {
                        'company_name': company,
                        'year': year,
                        'disruption_index': year_data['disruption_index'],
                        'pure_f_score': year_data['components']['pure_f_score'],
                        'quality_factor': year_data['components']['quality_factor'],
                        'impact_factor': year_data['components']['impact_factor'],
                        'total_patents': year_data['metrics']['total_patents'],
                        'total_citations': year_data['metrics']['total_citations'],
                        'citations_per_patent': year_data['metrics']['citations_per_patent'],
                        'matched_citations_per_patent': year_data['metrics']['matched_citations_per_patent'],
                        'high_quality_matches': year_data['quality_distribution']['high_quality_matches'],
                        'medium_quality_matches': year_data['quality_distribution']['medium_quality_matches'],
                        'low_quality_matches': year_data['quality_distribution']['low_quality_matches'],
                        'poor_quality_matches': year_data['quality_distribution']['poor_quality_matches']
                    }
                    panel_data.append(row)
            
            # Convert to DataFrame and sort
            df = pd.DataFrame(panel_data)
            df['year'] = pd.to_numeric(df['year'])
            df = df.sort_values(['company_name', 'year'])
            
            # Save to CSV
            output_file = self.base_path / "disruption_index_panel.csv"
            df.to_csv(output_file, index=False)
            
            self.logger.info(f"Created panel dataset with {len(df)} observations")
            self.logger.info(f"Companies: {df['company_name'].nunique()}")
            self.logger.info(f"Years: {df['year'].min()} to {df['year'].max()}")
            
        except Exception as e:
            self.logger.error(f"Error creating panel dataset: {str(e)}")

def main():
    """
    Main execution function for Disruption Index calculation.
    
    The function:
    1. Loads configuration from workflow_schema_cleaned.json
    2. Initializes DisruptionIndexCalculator
    3. Processes each company's Pure F data
    4. Calculates Disruption Index components
    5. Saves results and tracks progress
    
    Required files:
    - workflow_schema_cleaned.json
    - Data/company_name/pure_f_summary.json (for each company)
    
    Outputs:
    - Data/company_name/di_summary.json (for each company)
    - logs/disruption_index.log
    
    The Disruption Index provides a comprehensive measure of a company's
    technological impact, combining citation quality, quantity, and distribution.
    """
    # Load schema
    schema_path = Path('workflow_schema_cleaned.json')
    if not schema_path.exists():
        raise FileNotFoundError("Cleaned schema file not found")
        
    # Initialize calculator
    calculator = DisruptionIndexCalculator(schema_path)
    
    # Process each company
    companies = calculator.schema['config']['companies']
    
    # Setup progress tracking
    pbar = tqdm(companies, desc="Calculating Disruption Index", unit="company")
    stats = {'successful': [], 'failed': []}
    
    for company in pbar:
        pbar.set_description(f"Processing {company}")
        
        try:
            results = calculator.calculate_company_di(company)
            
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
    
    # Create panel dataset
    calculator.create_panel_dataset(stats)
    
    # Print summary
    print("\nDisruption Index Calculation Summary")
    print("=" * 50)
    print(f"Successfully processed: {len(stats['successful'])} companies")
    print(f"Failed to process: {len(stats['failed'])} companies")
    
    if stats['failed']:
        print("\nFailed companies:")
        for company in stats['failed']:
            print(f"- {company}")
            
    # Print panel dataset info
    panel_file = calculator.base_path / "disruption_index_panel.csv"
    if panel_file.exists():
        df = pd.read_csv(panel_file)
        print("\nPanel Dataset Summary")
        print("=" * 50)
        print(f"Total observations: {len(df)}")
        print(f"Companies: {df['company_name'].nunique()}")
        print(f"Year range: {df['year'].min()} to {df['year'].max()}")

if __name__ == "__main__":
    main()

