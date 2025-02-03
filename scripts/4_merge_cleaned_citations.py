import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from tqdm import tqdm

class CitationMerger:
    """
    Merges backward and forward patent citations for each company.
    
    Backward citations are patents that a focal patent cites (like references in a paper).
    Forward citations are newer patents that cite the focal patent (like papers citing your work).
    
    This merger combines both types of citations into a single dataset while preserving
    the direction of the citation and adding metadata for analysis.
    """
    
    def __init__(self, base_path: Path = Path("Data")):
        """
        Initialize the merger with path to data directory.
        Sets up logging to track processing status and errors.
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)
        Path("logs").mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/citation_merger.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.base_path = base_path

    def get_companies(self) -> List[str]:
        """
        Get list of company folders from the Data directory.
        
        Excludes special folders like 'backup' and 'summary', and hidden folders
        starting with '.'.
        
        Returns:
            List of company names as strings
        """
        return [d.name for d in self.base_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')
                and d.name not in ['backup_20250131', 'summary']]

    def merge_company_citations(self, company: str) -> bool:
        """
        Merge backward and forward citations for a specific company.
        
        For each company, this:
        1. Loads the processed backward citations (patents cited by the company)
        2. Loads the processed forward citations (patents citing the company)
        3. Combines them with proper labeling and metadata
        4. Saves the merged result as a parquet file
        
        Args:
            company: Name of the company to process
            
        Returns:
            bool: True if merge was successful, False otherwise
        """
        try:
            # Load backward citations
            backward_file = self.base_path / company / f"{company}_merged_backward_citations.parquet"
            if not backward_file.exists():
                self.logger.error(f"Backward citations not found for {company}")
                return False
                
            backward_df = pd.read_parquet(backward_file)
            self.logger.info(f"Loaded {len(backward_df)} backward citations for {company}")
            
            # Load forward citations
            forward_file = self.base_path / company / f"{company}_merged_forward_citations.parquet"
            if not forward_file.exists():
                self.logger.error(f"Forward citations not found for {company}")
                return False
                
            forward_df = pd.read_parquet(forward_file)
            self.logger.info(f"Loaded {len(forward_df)} forward citations for {company}")
            
            # Merge citations
            merged_df = self._merge_citations(backward_df, forward_df, company)
            
            # Save merged data
            output_file = self.base_path / company / f"{company}_merged_citations.parquet"
            merged_df.to_parquet(output_file, index=False)
            
            self.logger.info(f"Saved merged citations for {company}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error merging citations for {company}: {str(e)}")
            return False
            
    def _merge_citations(self, backward_df: pd.DataFrame, forward_df: pd.DataFrame, company: str) -> pd.DataFrame:
        """
        Merge backward and forward citations with proper labeling.
        
        This creates a unified citation network where:
        - For backward citations: company patent -> connected_patent
        - For forward citations: connected_patent -> company patent
        
        Args:
            backward_df: DataFrame of backward citations
            forward_df: DataFrame of forward citations
            company: Name of the company
            
        Returns:
            DataFrame with columns:
            - citing_patent_id: ID of the patent making the citation
            - connected_patent_id: ID of the cited/citing patent
            - citation_date: When the citation was made
            - citation_type: 'backward' or 'forward'
            - company: Name of the company
            - processing_date: When this data was processed
        """
        # Add citation type labels
        backward_df['citation_type'] = 'backward'
        forward_df['citation_type'] = 'forward'
        
        # Add company name
        backward_df['company'] = company
        forward_df['company'] = company
        
        # Standardize column names for connected patents
        backward_df = backward_df.rename(columns={'cited_patent_id': 'connected_patent_id'})
        forward_df = forward_df.rename(columns={'citing_patent_id': 'connected_patent_id'})
        
        # Combine the dataframes
        merged_df = pd.concat([backward_df, forward_df], ignore_index=True)
        
        # Add metadata
        merged_df['processing_date'] = datetime.now().strftime('%Y-%m-%d')
        
        return merged_df

def main():
    """
    Main execution function that processes all companies.
    
    Iterates through all companies, merges their citations, and provides
    a summary of successful and failed processing attempts.
    """
    merger = CitationMerger()
    companies = merger.get_companies()
    
    print(f"Processing {len(companies)} companies...")
    successful = []
    failed = []
    
    for company in tqdm(companies):
        if merger.merge_company_citations(company):
            successful.append(company)
            print(f"Successfully processed {company}")
        else:
            failed.append(company)
            print(f"Failed to process {company}")
    
    print(f"\nMerging Summary")
    print("=" * 50)
    print(f"Successfully merged: {len(successful)} companies")
    print(f"Failed to merge: {len(failed)} companies")
    
    if failed:
        print("\nFailed companies:")
        for company in failed:
            print(f"- {company}")

if __name__ == "__main__":
    main()
