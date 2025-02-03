import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from tqdm import tqdm

class ForwardCitationMatcher:
    """
    Matches and analyzes forward citations for company patents.
    
    This class efficiently processes citation data to generate statistics about:
    1. Forward citation counts (patents that cite this patent)
    2. Backward citation counts (patents cited by this patent)
    3. Citation date ranges and temporal patterns
    """
    
    def __init__(self, base_path: Path = Path("Data")):
        """Initialize the matcher with logging setup and base path."""
        # Setup logging
        self.logger = logging.getLogger(__name__)
        Path("logs").mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/forward_matching.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.base_path = base_path

    def get_companies(self) -> List[str]:
        """Get list of company folders from the Data directory."""
        return [d.name for d in self.base_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')
                and d.name not in ['backup_20250131', 'summary']]

    def rematch_company_citations(self, company: str) -> bool:
        """Process and analyze citations for a company."""
        try:
            self.logger.info(f"Starting to process {company}")
            
            # Load the merged citations data
            citations_file = self.base_path / company / f"{company}_merged_citations.parquet"
            if not citations_file.exists():
                self.logger.error(f"Merged citations file not found for {company}")
                return False
            
            self.logger.info(f"Loading citations for {company}")    
            citations_df = pd.read_parquet(citations_file)
            self.logger.info(f"Loaded {len(citations_df)} citations for {company}")
            
            # Generate citation analysis
            analysis_df = self._analyze_citations_efficient(citations_df, company)
            
            # Save the analysis results
            output_file = self.base_path / company / f"{company}_citation_analysis.parquet"
            self.logger.info(f"Saving analysis results for {company}")
            analysis_df.to_parquet(output_file, index=False)
            
            self.logger.info(f"Completed citation analysis for {company}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error analyzing citations for {company}: {str(e)}")
            return False
            
    def _analyze_citations_efficient(self, citations_df: pd.DataFrame, company: str) -> pd.DataFrame:
        """
        Efficiently analyze citation patterns using vectorized operations.
        
        This method uses pandas' optimized groupby operations to process all patents
        at once rather than iterating through them individually.
        """
        try:
            self.logger.info(f"{company}: Starting citation analysis with {len(citations_df)} citations")
            
            # Convert dates once
            citations_df['citation_date'] = pd.to_datetime(citations_df['citation_date'])
            self.logger.info(f"{company}: Dates converted")
            
            # Calculate backward citations (where patent is citing)
            self.logger.info(f"{company}: Calculating backward citations")
            backward_counts = citations_df[
                citations_df['citation_type'] == 'backward'
            ].groupby('citing_patent_id').size().to_frame('total_backward_citations')
            
            # Calculate forward citations (where patent is cited)
            self.logger.info(f"{company}: Calculating forward citations")
            forward_counts = citations_df[
                citations_df['citation_type'] == 'forward'
            ].groupby('connected_patent_id').size().to_frame('total_forward_citations')
            
            # Get all unique patents
            all_patents = pd.Index(set(citations_df['citing_patent_id']).union(
                                 set(citations_df['connected_patent_id'])))
            self.logger.info(f"{company}: Processing {len(all_patents)} unique patents")
            
            # Calculate date ranges for each patent
            self.logger.info(f"{company}: Calculating date ranges")
            date_ranges = citations_df.groupby('citing_patent_id').agg({
                'citation_date': ['min', 'max']
            })
            date_ranges.columns = ['earliest_citation', 'latest_citation']
            
            # Create base DataFrame with all patents
            results = pd.DataFrame(index=all_patents)
            results.index.name = 'patent_id'
            results = results.reset_index()
            
            # Join all the data
            self.logger.info(f"{company}: Combining results")
            results = results.merge(
                backward_counts, left_on='patent_id', right_index=True, how='left'
            ).merge(
                forward_counts, left_on='patent_id', right_index=True, how='left'
            ).merge(
                date_ranges, left_on='patent_id', right_index=True, how='left'
            )
            
            # Fill NaN values with 0 for citation counts
            results['total_backward_citations'] = results['total_backward_citations'].fillna(0)
            results['total_forward_citations'] = results['total_forward_citations'].fillna(0)
            
            # Add metadata
            results['company_name'] = company
            results['processing_date'] = datetime.now().strftime('%Y-%m-%d')
            
            return results
            
        except Exception as e:
            self.logger.error(f"{company}: Error in analysis process: {str(e)}")
            raise

def main():
    """Process all companies and generate citation analysis."""
    matcher = ForwardCitationMatcher()
    companies = matcher.get_companies()
    
    print(f"Processing {len(companies)} companies...")
    successful = []
    failed = []
    
    for company in tqdm(companies):
        if matcher.rematch_company_citations(company):
            successful.append(company)
            print(f"Successfully processed {company}")
        else:
            failed.append(company)
            print(f"Failed to process {company}")
    
    print(f"\nAnalysis Summary")
    print("=" * 50)
    print(f"Successfully analyzed: {len(successful)} companies")
    print(f"Failed to analyze: {len(failed)} companies")
    
    if failed:
        print("\nFailed companies:")
        for company in failed:
            print(f"- {company}")

if __name__ == "__main__":
    main()
