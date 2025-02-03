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
    
    def __init__(self, schema_path: Path = None):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/disruption_index.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load schema
        if schema_path:
            with open(schema_path) as f:
                self.schema = json.load(f)
        
        self.base_path = Path(self.schema['config']['base_path']) if schema_path else Path('Data')
        
    def calculate_company_di(self, company: str) -> Optional[Dict]:
        """Calculate Disruption Index for a company."""
        try:
            # Load citation analysis data
            analysis_file = self.base_path / company / "citation_analysis.json"
            pure_f_file = self.base_path / company / "pure_f_summary.json"
            
            if not analysis_file.exists() or not pure_f_file.exists():
                self.logger.error(f"Required files not found for {company}")
                return None

            with open(analysis_file, 'r') as f:
                citation_data = json.load(f)

            with open(pure_f_file, 'r') as f:
                pure_f_data = json.load(f)
            
            # Debug: print first year data structure
            first_year = list(citation_data.keys())[0]
            print(f"\nProcessing {company} - Year {first_year}")
            print(f"Citation data structure: {json.dumps(citation_data[first_year], indent=2)}")
            print(f"Pure F data structure: {json.dumps(pure_f_data[first_year], indent=2)}")

            # Calculate DI by year
            yearly_results = {}
            for year in citation_data.keys():
                if year in pure_f_data:
                    year_citation = citation_data[year]
                    year_pure_f = pure_f_data[year]
                    
                    di_score = self._calculate_year_di(
                        year_pure_f,
                        year_citation,
                        company,
                        int(year)
                    )
                    if di_score:
                        yearly_results[year] = di_score

            if not yearly_results:
                self.logger.error(f"No valid DI results calculated for {company}")
                return None

            # Save results
            output_file = self.base_path / company / "disruption_index.json"
            with open(output_file, 'w') as f:
                json.dump(yearly_results, f, indent=2)

            return yearly_results

        except Exception as e:
            self.logger.error(f"Error calculating DI for {company}: {str(e)}")
            return None

    def _calculate_year_di(self, pure_f_data: Dict, citation_data: Dict, 
                         company: str, year: int) -> Optional[Dict]:
        """Calculate both DI and mDI for a specific year."""
        try:
            # Extract metrics from citation data
            basic_metrics = citation_data['basic_metrics']
            temporal_metrics = citation_data['temporal_metrics']
            network_metrics = citation_data['network_metrics']
            
            # Get Pure F score
            pure_f_score = pure_f_data.get('pure_f_score', 0.0)
            
            # Calculate components
            j5 = self._calculate_j5(basic_metrics, pure_f_score)
            i5 = self._calculate_i5(temporal_metrics)
            k5 = self._calculate_k5(network_metrics)
            
            # Calculate indices
            di_score = (j5 + i5 + k5) / 3.0
            mdi_score = j5 * (1 + i5) * (1 + k5)
            
            return {
                'company_name': company,
                'year': year,
                'disruption_index': float(di_score),
                'modified_disruption_index': float(mdi_score),
                'components': {
                    'j5_score': float(j5),
                    'i5_score': float(i5),
                    'k5_score': float(k5)
                },
                'metrics': {
                    'pure_f_score': float(pure_f_score),
                    'total_citations': int(basic_metrics.get('total_citations', 0)),
                    'network_density': float(network_metrics.get('network_density', 0.0))
                },
                'processing_date': datetime.now().strftime('%Y-%m-%d')
            }

        except Exception as e:
            self.logger.error(f"Error in DI calculation: {str(e)}")
            return None

    def _calculate_j5(self, metrics: Dict, pure_f_score: float) -> float:
        """Calculate forward citation impact score (j5)."""
        try:
            total_citations = metrics.get('total_citations', 0)
            citing_patents = metrics.get('unique_citing_patents', 1)  # avoid div by zero
            
            if citing_patents > 0:
                citation_impact = total_citations / citing_patents
                return min(1.0, citation_impact * pure_f_score)
            return 0.0
        except:
            return 0.0

    def _calculate_i5(self, temporal_metrics: Dict) -> float:
        """Calculate development speed score (i5)."""
        try:
            mean_lag = temporal_metrics.get('mean_citation_lag', 0)
            if mean_lag > 0:
                speed_factor = 1.0 / (1.0 + mean_lag/5.0)  # 5-year normalization
                return min(1.0, speed_factor)
            return 0.0
        except:
            return 0.0

    def _calculate_k5(self, network_metrics: Dict) -> float:
        """Calculate citation diversity score (k5)."""
        try:
            # Use pre-calculated k5 diversity score if available
            k5_diversity = network_metrics.get('k5_diversity', 0.0)
            return min(1.0, k5_diversity)
        except:
            return 0.0

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
                di_file = self.base_path / company / "disruption_index.json"
                
                if not di_file.exists():
                    self.logger.warning(f"DI summary file not found for {company}")
                    continue
                    
                with open(di_file) as f:
                    di_data = json.load(f)
                
                # Extract yearly data
                for year, year_data in di_data.items():
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
    """Process all companies and calculate Disruption Index."""
    # Initialize calculator with default Data path
    calculator = DisruptionIndexCalculator()
    
    # Get list of companies (directories in Data path)
    companies = [d.name for d in calculator.base_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')
                and d.name not in ['backup', 'summary']]  # exclude special directories
    
    print(f"Processing {len(companies)} companies...")
    successful = []
    failed = []
    
    # Process each company
    for company in tqdm(companies):
        if calculator.calculate_company_di(company):
            successful.append(company)
            print(f"Successfully processed {company}")
        else:
            failed.append(company)
            print(f"Failed to process {company}")
    
    print(f"\nDisruption Index Calculation Summary")
    print("=" * 50)
    print(f"Successfully processed: {len(successful)} companies")
    print(f"Failed to process: {len(failed)} companies")
    
    if failed:
        print("\nFailed companies:")
        for company in failed:
            print(f"- {company}")

if __name__ == "__main__":
    main()

