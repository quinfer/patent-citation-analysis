import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm

class ForwardCitationProcessor:
    """Process forward citations from focal company data"""
    
    def __init__(self, base_path: Path = Path("Data")):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        Path("logs").mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/forward_citations.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.base_path = base_path

    def get_companies(self) -> List[str]:
        """Get list of companies from Data directory."""
        return [d.name for d in self.base_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')
                and d.name not in ['backup_20250131', 'summary']]

    def _get_citation_files(self, company: str) -> List[Path]:
        """Get citation files for a company, checking both formats."""
        citation_dir = self.base_path / company / "Forward citation"
        
        # First check for raw numbered files
        raw_files = list(citation_dir.glob("[0-9]*_[0-9]*.csv"))
        if raw_files:
            return raw_files
        
        # If no raw files, check for consolidated file
        consolidated_file = citation_dir / f"{company}_forward_citations.csv"
        if consolidated_file.exists():
            return [consolidated_file]
        
        return []

    def process_citation_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Process a citation file from either format."""
        try:
            # Check if this is a consolidated file by looking at the filename
            is_consolidated = file_path.name.endswith('_forward_citations.csv')
            
            if is_consolidated:
                # Read consolidated format (comma-separated)
                df = pd.read_csv(
                    file_path,
                    dtype={
                        'focal_patent': str,
                        'citing_patent': str,
                        'citation_date': str
                    }
                )
                # Rename columns to match our standard format
                df = df.rename(columns={
                    'focal_patent': 'cited_patent_id',
                    'citing_patent': 'citing_patent_id'
                })
            else:
                # Read raw format (semicolon-separated)
                df = pd.read_csv(
                    file_path, 
                    delimiter=';',
                    dtype={
                        'citing_patent_id': str,
                        'citing_number': str,
                        'forward_cited_number': str,
                        'forward_cited_date': str
                    },
                    low_memory=False
                )
                
                # Process raw format columns
                if 'citing_patent_id' not in df.columns:
                    df = df.rename(columns={'citing_number': 'cited_patent_id'})
                df = df.rename(columns={
                    'forward_cited_number': 'citing_patent_id',
                    'forward_cited_date': 'citation_date'
                })
            
            # Common processing for both formats
            df['citation_date'] = pd.to_datetime(df['citation_date'], errors='coerce')
            df['citing_patent_id'] = df['citing_patent_id'].astype(str)
            df['cited_patent_id'] = df['cited_patent_id'].astype(str)
            
            # Select only required columns
            required_cols = ['citing_patent_id', 'cited_patent_id', 'citation_date']
            if not all(col in df.columns for col in required_cols):
                self.logger.error(f"Missing required columns in {file_path}")
                return None
                
            return df[required_cols]
                
        except Exception as e:
            self.logger.error(f"Failed to process {file_path}: {str(e)}")
            return None

    def process_company(self, company: str) -> bool:
        """Process all citation files for a company."""
        self.logger.info(f"Processing {company}")
        
        # Get citation files for the company
        files = self._get_citation_files(company)
            
        if not files:
            self.logger.warning(f"No citation files found for {company}")
            return False
            
        # Process each file
        dfs = []
        for file in files:
            df = self.process_citation_file(file)
            if df is not None:
                dfs.append(df)
                self.logger.info(f"Successfully processed {file.name}: {len(df)} rows")
        
        if not dfs:
            self.logger.error(f"No valid citation data found for {company}")
            return False
            
        # Combine and save
        combined_df = pd.concat(dfs, ignore_index=True)
        output_file = self.base_path / company / f"{company}_merged_forward_citations.parquet"
        combined_df.to_parquet(output_file, index=False)
        
        self.logger.info(f"Successfully processed {company}: {len(combined_df)} total citations")
        return True

def main():
    processor = ForwardCitationProcessor()
    companies = processor.get_companies()
    
    print(f"Processing {len(companies)} companies...")
    successful = []
    failed = []
    
    for company in tqdm(companies):
        if processor.process_company(company):
            successful.append(company)
            print(f"Successfully processed {company}")
        else:
            failed.append(company)
            print(f"Failed to process {company}")
    
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
