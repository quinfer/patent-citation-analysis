import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from tqdm import tqdm

class CitationMerger:
    """Merge processed backward and forward citations"""
    
    def __init__(self, schema_path: Path):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/citation_merger.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load schema
        with open(schema_path) as f:
            self.schema = json.load(f)
        
        self.base_path = Path(self.schema['config']['base_path'])
        
    def merge_company_citations(self, company: str) -> Optional[pd.DataFrame]:
        """Merge backward and forward citations for a company"""
        try:
            # Load backward citations
            backward_file = self.base_path / company / "Backward citation" / f"{company}_backward_citations.csv"
            if not backward_file.exists():
                self.logger.error(f"Backward citations not found for {company}")
                return None
                
            backward_df = pd.read_csv(backward_file, dtype={'focal_patent': str, 'cited_patent': str})
            self.logger.info(f"Loaded {len(backward_df)} backward citations for {company}")
            
            # Load forward citations
            forward_file = self.base_path / company / "Forward citation" / f"{company}_forward_citations.csv"
            if not forward_file.exists():
                self.logger.error(f"Forward citations not found for {company}")
                return None
                
            forward_df = pd.read_csv(forward_file, dtype={'focal_patent': str, 'citing_patent': str})
            self.logger.info(f"Loaded {len(forward_df)} forward citations for {company}")
            
            # Merge citations
            merged_df = self._merge_citations(backward_df, forward_df, company)
            
            # Save merged data
            output_folder = self.base_path / company
            output_file = output_folder / "merged_cleaned_data.csv"
            merged_df.to_csv(output_file, index=False)
            
            self.logger.info(f"Saved merged citations for {company}")
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Error merging citations for {company}: {str(e)}")
            return None
            
    def _merge_citations(self, backward_df: pd.DataFrame, forward_df: pd.DataFrame, company: str) -> pd.DataFrame:
        """Merge backward and forward citations with proper labeling"""
        # Add citation type labels
        backward_df['citation_type'] = 'backward'
        forward_df['citation_type'] = 'forward'
        
        # Standardize column names
        backward_df = backward_df.rename(columns={'cited_patent': 'connected_patent'})
        forward_df = forward_df.rename(columns={'citing_patent': 'connected_patent'})
        
        # Combine the dataframes
        merged_df = pd.concat([backward_df, forward_df], ignore_index=True)
        
        # Add metadata
        merged_df['processing_date'] = datetime.now().strftime('%Y-%m-%d')
        
        return merged_df

def main():
    """Main execution function"""
    # Load schema
    schema_path = Path('workflow_schema_cleaned.json')
    if not schema_path.exists():
        raise FileNotFoundError("Cleaned schema file not found")
        
    # Initialize merger
    merger = CitationMerger(schema_path)
    
    # Process each company
    companies = merger.schema['config']['companies']
    
    # Setup progress tracking
    pbar = tqdm(companies, desc="Merging Citations", unit="company")
    stats = {'successful': [], 'failed': []}
    
    for company in pbar:
        pbar.set_description(f"Processing {company}")
        
        try:
            merged_df = merger.merge_company_citations(company)
            
            if merged_df is not None:
                stats['successful'].append(company)
                pbar.set_postfix(status="Success")
            else:
                stats['failed'].append(company)
                pbar.set_postfix(status="Failed")
                
        except Exception as e:
            merger.logger.error(f"Failed to merge {company}: {str(e)}")
            stats['failed'].append(company)
            pbar.set_postfix(status="Error")
            continue
    
    # Print summary
    print("\nMerging Summary")
    print("=" * 50)
    print(f"Successfully merged: {len(stats['successful'])} companies")
    print(f"Failed to merge: {len(stats['failed'])} companies")
    
    if stats['failed']:
        print("\nFailed companies:")
        for company in stats['failed']:
            print(f"- {company}")

if __name__ == "__main__":
    main()
