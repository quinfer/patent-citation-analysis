import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from tqdm import tqdm

class PureFCalculator:
    """
    Enhanced Pure F score calculator with temporal and network adjustments.
    
    Pure F Score calculation now includes:
    1. Basic citation matching rate
    2. Temporal weighting (newer citations weighted higher)
    3. Network position adjustment
    4. Citation quality factors
    """
    
    def __init__(self, base_path: Path = Path("Data")):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        Path("logs").mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/pure_f_calculation.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.base_path = base_path

    def calculate_company_pure_f(self, company: str) -> Optional[Dict]:
        """Calculate enhanced Pure F scores for a company."""
        try:
            # Load citation analysis data
            analysis_file = self.base_path / company / "citation_analysis.json"
            if not analysis_file.exists():
                self.logger.error(f"Citation analysis file not found for {company}")
                return None

            with open(analysis_file, 'r') as f:
                citation_data = json.load(f)

            # Calculate Pure F scores by year
            yearly_results = {}
            for year, year_data in citation_data.items():
                self.logger.info(f"Processing year {year} for {company}")
                
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

    def _calculate_year_pure_f(self, year_data: Dict, company: str, year: int) -> Optional[Dict]:
        """
        Calculate Pure F score for a specific year with enhanced metrics.
        
        New formula:
        Pure F = (Base Match Rate) * (Temporal Factor) * (Network Factor) * (Quality Factor)
        """
        try:
            # Extract metrics from year_data
            basic_metrics = year_data['basic_metrics']
            temporal_metrics = year_data['temporal_metrics']
            network_metrics = year_data['network_metrics']
            
            # Calculate base match rate
            total_citations = basic_metrics['total_citations']
            if total_citations == 0:
                return None
                
            # Calculate temporal factor (weight recent citations higher)
            temporal_factor = self._calculate_temporal_factor(temporal_metrics)
            
            # Calculate network factor
            network_factor = self._calculate_network_factor(network_metrics)
            
            # Calculate quality factor
            quality_factor = self._calculate_quality_factor(basic_metrics)
            
            # Calculate final Pure F score
            pure_f_score = temporal_factor * network_factor * quality_factor
            
            return {
                'company_name': company,
                'year': year,
                'pure_f_score': float(pure_f_score),
                'components': {
                    'temporal_factor': float(temporal_factor),
                    'network_factor': float(network_factor),
                    'quality_factor': float(quality_factor)
                },
                'metrics': {
                    'total_citations': total_citations,
                    'unique_citing_patents': basic_metrics['unique_citing_patents'],
                    'unique_cited_patents': basic_metrics['unique_cited_patents']
                },
                'processing_date': datetime.now().strftime('%Y-%m-%d')
            }

        except Exception as e:
            self.logger.error(f"Error calculating year {year} Pure F for {company}: {str(e)}")
            return None

    def _calculate_temporal_factor(self, temporal_metrics: Dict) -> float:
        """Calculate temporal weighting factor."""
        try:
            # Weight recent citations higher
            mean_lag = temporal_metrics.get('mean_citation_lag', 0)
            if mean_lag > 0:
                return 1.0 / (1.0 + mean_lag/10.0)  # Decay factor for older citations
            return 1.0
        except:
            return 1.0

    def _calculate_network_factor(self, network_metrics: Dict) -> float:
        """Calculate network position factor."""
        try:
            # Consider network density and connectivity
            density = network_metrics.get('network_density', 0)
            return min(1.0, 0.5 + density)  # Scale density to 0.5-1.0 range
        except:
            return 1.0

    def _calculate_quality_factor(self, basic_metrics: Dict) -> float:
        """Calculate citation quality factor."""
        try:
            # Consider citation density and diversity
            citing_patents = basic_metrics.get('unique_citing_patents', 0)
            cited_patents = basic_metrics.get('unique_cited_patents', 0)
            total_citations = basic_metrics.get('total_citations', 0)
            
            if citing_patents > 0 and cited_patents > 0:
                diversity = min(citing_patents, cited_patents) / max(citing_patents, cited_patents)
                density = total_citations / (citing_patents * cited_patents)
                return (diversity + density) / 2
            return 0.5
        except:
            return 0.5

def main():
    """Process all companies and calculate Pure F scores."""
    calculator = PureFCalculator()
    
    # Get list of companies
    companies = [d.name for d in calculator.base_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')
                and d.name not in ['backup', 'summary']]
    
    print(f"Processing {len(companies)} companies...")
    successful = []
    failed = []
    
    for company in tqdm(companies):
        if calculator.calculate_company_pure_f(company):
            successful.append(company)
            print(f"Successfully processed {company}")
        else:
            failed.append(company)
            print(f"Failed to process {company}")
    
    print(f"\nPure F Calculation Summary")
    print("=" * 50)
    print(f"Successfully processed: {len(successful)} companies")
    print(f"Failed to process: {len(failed)} companies")
    
    if failed:
        print("\nFailed companies:")
        for company in failed:
            print(f"- {company}")

if __name__ == "__main__":
    main()
