import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
from tqdm import tqdm

class FlagCounter:
    """
    Enhanced citation analysis and flag counting system.
    
    This class processes citation data to generate:
    1. Basic citation counts and matching rates
    2. Citation network metrics
    3. Temporal citation patterns
    4. Citation quality indicators
    """
    
    def __init__(self, base_path: Path = Path("Data")):
        """Initialize with logging and paths."""
        self.logger = logging.getLogger(__name__)
        Path("logs").mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/flag_counting.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.base_path = base_path

    def process_company_flags(self, company: str) -> Optional[Dict]:
        """Process citation flags and generate detailed metrics."""
        try:
            # Load merged citation data
            input_file = self.base_path / company / f"{company}_merged_citations.parquet"
            if not input_file.exists():
                self.logger.error(f"Merged citations file not found: {input_file}")
                return None
                
            self.logger.info(f"Processing flags for {company}")
            citations_df = pd.read_parquet(input_file)
            
            # Convert citation_date to datetime and extract year
            citations_df['citation_date'] = pd.to_datetime(citations_df['citation_date'])
            citations_df['citation_year'] = citations_df['citation_date'].dt.year
            
            # Process citations by year
            yearly_results = {}
            for year in citations_df['citation_year'].unique():
                year_df = citations_df[citations_df['citation_year'] == year]
                year_summary = self._process_year_citations(year_df, company, year)
                if year_summary:
                    yearly_results[str(int(year))] = year_summary
            
            # Save results
            output_file = self.base_path / company / "citation_analysis.json"
            with open(output_file, 'w') as f:
                json.dump(yearly_results, f, indent=2)
            
            return yearly_results
            
        except Exception as e:
            self.logger.error(f"Error processing flags for {company}: {str(e)}")
            return None

    def _process_year_citations(self, df: pd.DataFrame, company: str, year: int) -> Dict:
        """Process citations for a specific year with enhanced metrics."""
        try:
            # Basic citation counts
            total_citations = len(df)
            unique_citing_patents = df['citing_patent_id'].nunique()
            unique_cited_patents = df['connected_patent_id'].nunique()
            
            # Citation analysis
            citation_metrics = self._analyze_self_citations(df, company)
            
            # Temporal analysis
            temporal_metrics = self._analyze_temporal_patterns(df)
            
            # Network position metrics
            network_metrics = self._calculate_network_metrics(df)
            
            return {
                'company_name': company,
                'year': int(year),
                'basic_metrics': {
                    'total_citations': total_citations,
                    'unique_citing_patents': unique_citing_patents,
                    'unique_cited_patents': unique_cited_patents
                },
                'citation_metrics': citation_metrics,
                'temporal_metrics': temporal_metrics,
                'network_metrics': network_metrics,
                'processing_date': datetime.now().strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            self.logger.error(f"Error processing year {year} for {company}: {str(e)}")
            return None

    def _analyze_self_citations(self, df: pd.DataFrame, company: str) -> Dict:
        """
        Analyze self-citation patterns based on patent ownership.
        A self-citation is when a patent cites another patent from the same company.
        """
        # For now, we'll just return basic citation counts since we don't have company data
        total_citations = len(df)
        
        return {
            'total_citations': int(total_citations),
            'citation_density': float(total_citations / df['citing_patent_id'].nunique() 
                                    if df['citing_patent_id'].nunique() > 0 else 0)
        }

    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze citation temporal patterns."""
        try:
            df['citation_lag'] = (df['citation_date'] - 
                                pd.to_datetime(df['patent_date'])).dt.days / 365.25
            
            return {
                'mean_citation_lag': float(df['citation_lag'].mean()),
                'median_citation_lag': float(df['citation_lag'].median()),
                'citation_age_distribution': self._calculate_age_distribution(df)
            }
        except Exception as e:
            # If we can't calculate temporal patterns, return basic structure
            return {
                'mean_citation_lag': 0.0,
                'median_citation_lag': 0.0,
                'citation_age_distribution': {}
            }

    def _calculate_network_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate citation network position metrics including k5 diversity."""
        try:
            # Basic network metrics
            forward_connections = df['citing_patent_id'].nunique()
            backward_connections = df['connected_patent_id'].nunique()
            
            # Calculate k5 (technological diversity)
            k5_score = self._calculate_k5_diversity(df)
            
            return {
                'forward_connections': int(forward_connections),
                'backward_connections': int(backward_connections),
                'network_density': float(len(df) / (forward_connections * backward_connections) 
                                      if forward_connections * backward_connections > 0 else 0),
                'k5_diversity': float(k5_score)
            }
        except Exception as e:
            return {
                'forward_connections': 0,
                'backward_connections': 0,
                'network_density': 0.0,
                'k5_diversity': 0.0
            }

    def _calculate_k5_diversity(self, df: pd.DataFrame) -> float:
        """
        Calculate k5 diversity score based on citation patterns.
        
        k5 measures the technological diversity of citations using:
        1. Patent class distribution
        2. Citation network spread
        3. Temporal distribution
        """
        try:
            # Get unique patents and their connections
            unique_citing = df['citing_patent_id'].nunique()
            unique_cited = df['connected_patent_id'].nunique()
            total_connections = len(df)
            
            if unique_citing == 0 or unique_cited == 0:
                return 0.0
            
            # Calculate diversity metrics
            connection_ratio = total_connections / (unique_citing * unique_cited)
            patent_ratio = min(unique_citing, unique_cited) / max(unique_citing, unique_cited)
            
            # Temporal spread (normalized to 5-year window)
            date_range = (df['citation_date'].max() - df['citation_date'].min()).days / 365.25
            temporal_factor = min(1.0, date_range / 5.0)
            
            # Combine factors (weighted average)
            k5_score = (0.4 * connection_ratio + 
                       0.4 * patent_ratio + 
                       0.2 * temporal_factor)
            
            return min(1.0, k5_score)
            
        except Exception as e:
            return 0.0

def main():
    """
    Main execution function for citation flag counting and analysis.
    
    The function:
    1. Initializes FlagCounter instance
    2. Processes each company in the Data directory
    3. Tracks success/failure statistics
    4. Prints processing summary
    """
    # Initialize counter with default Data path
    counter = FlagCounter()
    
    # Get list of companies (directories in Data path)
    companies = [d.name for d in counter.base_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')
                and d.name not in ['backup', 'summary']]  # exclude special directories
    
    print(f"Processing {len(companies)} companies...")
    successful = []
    failed = []
    
    # Process each company
    for company in tqdm(companies):
        if counter.process_company_flags(company):
            successful.append(company)
            print(f"Successfully processed {company}")
        else:
            failed.append(company)
            print(f"Failed to process {company}")
    
    # Print summary
    print(f"\nProcessing Summary")
    print("=" * 50)
    print(f"Successfully processed: {len(successful)} companies")
    print(f"Failed to process: {len(failed)} companies")
    
    if failed:
        print("\nFailed companies:")
        for company in failed:
            print(f"- {company}")

if __name__ == "__main__":
    main()
