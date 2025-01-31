import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from tqdm import tqdm

class ForwardCitationProcessor:
    """Process forward citations from cleaned focal company data"""
    
    def __init__(self, schema_path: Path):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/forward_citations.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load schema
        with open(schema_path) as f:
            self.schema = json.load(f)
        
        self.base_path = Path(self.schema['config']['base_path'])
        
    def process_company_citations(self, company: str) -> Optional[pd.DataFrame]:
        """Process forward citations for a single company"""
        try:
            # Load cleaned company data
            input_file = self.base_path / company / f"{company}_cleaned.csv"
            if not input_file.exists():
                self.logger.error(f"Cleaned file not found for {company}")
                return None
                
            # Read with explicit dtypes
            df = pd.read_csv(
                input_file,
                dtype={
                    'citing_patent_id': str,
                    'backward_cited_numbers': str,
                    'backward_cited_dates': str,
                    'forward_cited_numbers': str,
                    'forward_cited_dates': str,
                    'citing_number': str,
                    'ipc_code': str,
                },
                low_memory=False
            )
            
            # Extract forward citations
            citations_df = self._extract_forward_citations(df, company)
            
            # Save processed citations
            output_folder = self.base_path / company / "Forward citation"
            output_folder.mkdir(exist_ok=True)
            output_file = output_folder / f"{company}_forward_citations.csv"
            citations_df.to_csv(output_file, index=False)
            
            self.logger.info(f"Processed {len(citations_df)} forward citations for {company}")
            return citations_df
            
        except Exception as e:
            self.logger.error(f"Error processing {company}: {str(e)}")
            return None
            
    def _extract_forward_citations(self, df: pd.DataFrame, company: str) -> pd.DataFrame:
        """Extract and format forward citations from company data"""
        citation_data = []
        
        for _, row in df.iterrows():
            # Handle potential NaN values
            forward_numbers = str(row['forward_cited_numbers'])
            forward_dates = str(row['forward_cited_dates'])
            
            if pd.notna(forward_numbers) and forward_numbers.strip():
                numbers = forward_numbers.split(', ')
                dates = forward_dates.split(', ')
                
                # Match citations with dates
                for cited_num, cited_date in zip(numbers, dates):
                    if cited_num.strip():  # Ensure non-empty citation
                        citation_data.append({
                            'focal_patent': row['citing_patent_id'],
                            'citing_patent': cited_num.strip(),
                            'citation_date': cited_date.strip(),
                            'company_name': company
                        })
        
        citations_df = pd.DataFrame(citation_data)
        return citations_df

def main():
    """Main execution function"""
    # Load schema
    schema_path = Path('workflow_schema_cleaned.json')
    if not schema_path.exists():
        raise FileNotFoundError("Cleaned schema file not found")
        
    # Initialize processor
    processor = ForwardCitationProcessor(schema_path)
    
    # Process each company
    companies = processor.schema['config']['companies']
    
    # Setup progress tracking
    pbar = tqdm(companies, desc="Processing Companies", unit="company")
    stats = {'successful': [], 'failed': []}
    
    for company in pbar:
        pbar.set_description(f"Processing {company}")
        
        try:
            citations_df = processor.process_company_citations(company)
            
            if citations_df is not None:
                stats['successful'].append(company)
                pbar.set_postfix(status="Success")
            else:
                stats['failed'].append(company)
                pbar.set_postfix(status="Failed")
                
        except Exception as e:
            processor.logger.error(f"Failed to process {company}: {str(e)}")
            stats['failed'].append(company)
            pbar.set_postfix(status="Error")
            continue
    
    # Print summary
    print("\nProcessing Summary")
    print("=" * 50)
    print(f"Successfully processed: {len(stats['successful'])} companies")
    print(f"Failed to process: {len(stats['failed'])} companies")
    
    if stats['failed']:
        print("\nFailed companies:")
        for company in stats['failed']:
            print(f"- {company}")

if __name__ == "__main__":
    main()
