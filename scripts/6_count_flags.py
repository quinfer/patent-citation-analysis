import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from tqdm import tqdm

class FlagCounter:
    """
    A class to analyze and summarize citation matching results by year.
    
    This class processes the citation matching results from step 5 and generates yearly summaries.
    It handles:
    1. Loading citation matching data from flag_count.csv files
    2. Aggregating and analyzing citation matches by year
    3. Calculating quality metrics and statistics
    4. Saving summarized results to flag_summary.json
    
    Attributes:
        logger: Logging instance for tracking process and errors
        schema: Configuration schema loaded from JSON
        base_path: Base directory path for data files
    """
    
    def __init__(self, schema_path: Path):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/flag_counting.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load schema
        with open(schema_path) as f:
            self.schema = json.load(f)
        
        self.base_path = Path(self.schema['config']['base_path'])
        
    def process_company_flags(self, company: str) -> Optional[Dict]:
        """
        Process and analyze citation matching flags for a company, organized by year.
        
        Args:
            company (str): Name of the company to process
            
        Returns:
            Optional[Dict]: Dictionary containing yearly citation matching summaries, or None if processing fails
            
        The function:
        1. Loads citation matching results from flag_count.csv
        2. Retrieves patent grant years from company_cleaned.csv
        3. Merges the data to organize citations by year
        4. Processes each year's data separately
        5. Saves results to flag_summary.json
        
        Example output structure:
        {
            "2020": {
                "company_name": "company_x",
                "year": 2020,
                "total_patents": 100,
                "total_forward_citations": 500,
                "matched_citations": 450,
                ...
            },
            "2021": {
                ...
            }
        }
        """
        try:
            # Load flag count data
            input_file = self.base_path / company / "flag_count.csv"
            
            if not input_file.exists():
                self.logger.error(f"Flag count file not found: {input_file}")
                return None
                
            self.logger.info(f"Processing flags for {company}")
            
            # Read the data
            df = pd.read_csv(input_file)
            
            # Load oracle data to get years
            oracle_file = self.base_path / company / f"{company}_cleaned.csv"
            oracle_df = pd.read_csv(oracle_file)
            
            # Extract year from granted_date in oracle_df
            oracle_df['year'] = pd.to_datetime(oracle_df['granted_date']).dt.year
            
            # Rename columns for merge
            oracle_df = oracle_df.rename(columns={'citing_patent_id': 'patent_id'})
            
            # Merge flag data with oracle data to get years
            df = df.merge(oracle_df[['patent_id', 'year']], on='patent_id', how='left')
            
            if df['year'].isna().all():
                self.logger.error(f"No year data found after merge for {company}")
                return None
            
            # Process by year
            yearly_results = {}
            for year in df['year'].dropna().unique():
                year_df = df[df['year'] == year]
                year_summary = self._process_year_flags(year_df, company, year)
                yearly_results[str(int(year))] = year_summary
            
            # Save results
            self._save_results(yearly_results, company)
            
            return yearly_results
            
        except Exception as e:
            self.logger.error(f"Error processing flags for {company}: {str(e)}")
            return None
            
    def _process_year_flags(self, df: pd.DataFrame, company: str, year: int) -> Optional[Dict]:
        """Process flags for a specific year"""
        try:
            # Add debugging to see what data we're getting
            self.logger.info(f"Processing year {year} for {company}")
            self.logger.info(f"Number of patents: {len(df)}")
            self.logger.info(f"Sample data:\n{df.head().to_dict('records')}")
            
            # Basic data validation
            if df.empty:
                self.logger.warning(f"No data for {company} in year {year}")
                return None
            
            # Validate required columns
            required_columns = ['total_forward_citations', 'matched_citations', 'match_rate']
            if not all(col in df.columns for col in required_columns):
                self.logger.error(f"Missing required columns for {company}, year {year}")
                self.logger.error(f"Available columns: {df.columns.tolist()}")
                return None
            
            # Calculate year summary
            year_summary = {
                'company_name': company,
                'year': int(year),
                'total_patents': int(len(df)),
                'total_forward_citations': int(df['total_forward_citations'].sum()),
                'matched_citations': int(df['matched_citations'].sum()),
                'average_match_rate': float(df['match_rate'].mean()),
                'patents_with_perfect_match': int(len(df[df['match_rate'] == 1.0])),
                'patents_with_no_match': int(len(df[df['match_rate'] == 0.0])),
                'processing_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Validate the summary (ensure we're not returning empty/invalid data)
            if year_summary['total_patents'] == 0:
                self.logger.warning(f"No patents found for {company} in year {year}")
                return None
            
            self.logger.info(f"Successfully processed year {year} for {company}")
            self.logger.info(f"Year summary: {year_summary}")
            
            return year_summary
            
        except Exception as e:
            self.logger.error(f"Error processing year {year} for {company}: {str(e)}")
            self.logger.exception("Detailed traceback:")
            return None
            
    def _process_flag_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """
        Process a subset of citation matching data to calculate additional metrics.
        
        Args:
            chunk (pd.DataFrame): DataFrame containing citation matching data
            
        Returns:
            pd.DataFrame: Processed DataFrame with additional columns:
                - unmatched_citations: Number of citations that couldn't be matched
                - match_percentage: Percentage of citations successfully matched
                - match_quality: Categorical rating of match quality
                
        The function:
        1. Calculates unmatched citations (total - matched)
        2. Computes match percentage
        3. Categorizes match quality into Poor/Fair/Good/Excellent
        
        Match quality categories:
        - Poor: 0-25% match rate
        - Fair: 26-50% match rate
        - Good: 51-75% match rate
        - Excellent: 76-100% match rate
        """
        # Calculate additional metrics
        chunk['unmatched_citations'] = chunk['total_forward_citations'] - chunk['matched_citations']
        chunk['match_percentage'] = (chunk['matched_citations'] / chunk['total_forward_citations'] * 100).round(2)
        
        # Categorize matching quality
        chunk['match_quality'] = pd.cut(
            chunk['match_percentage'],
            bins=[0, 25, 50, 75, 100],
            labels=['Poor', 'Fair', 'Good', 'Excellent']
        )
        
        return chunk
        
    def _calculate_company_summary(self, df: pd.DataFrame, company: str) -> Dict:
        """
        Calculate company-level summary statistics with proper type conversion.
        
        Args:
            df (pd.DataFrame): DataFrame containing all citation matching data for a company
            company (str): Name of the company
            
        Returns:
            Dict: Company-level summary statistics with proper Python types
            
        The function:
        1. Calculates overall company metrics
        2. Converts numpy types to Python types for JSON compatibility
        3. Generates match quality distribution
        
        Example output structure:
        {
            "company_name": "company_x",
            "total_patents": 150,
            "total_forward_citations": 750,
            "total_matched_citations": 675,
            "total_unmatched_citations": 75,
            "average_match_rate": 90.0,
            "match_quality_distribution": {
                "Excellent": 120,
                "Good": 20,
                "Fair": 10,
                "Poor": 0
            },
            "patents_with_perfect_match": 120,
            "patents_with_no_match": 0,
            "processing_date": "2025-01-30"
        }
        """
        summary = {
            'company_name': company,
            'total_patents': int(len(df)),  # Convert to regular Python int
            'total_forward_citations': int(df['total_forward_citations'].sum()),
            'total_matched_citations': int(df['matched_citations'].sum()),
            'total_unmatched_citations': int(df['unmatched_citations'].sum()),
            'average_match_rate': float(df['match_percentage'].mean()),  # Convert to float
            'match_quality_distribution': {
                k: int(v) for k, v in df['match_quality'].value_counts().to_dict().items()
            },
            'processing_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Convert these to regular Python ints
        summary['patents_with_perfect_match'] = int(len(df[df['match_percentage'] == 100]))
        summary['patents_with_no_match'] = int(len(df[df['match_percentage'] == 0]))
        
        return summary
        
    def _save_results(self, results: Dict, company: str):
        """
        Save processed citation matching results to JSON file.
        
        Args:
            results (Dict): Dictionary containing processed results
            company (str): Name of the company
            
        The function:
        1. Creates flag_summary.json in company directory
        2. Saves results with proper indentation
        3. Logs success or failure
        
        Output file: Data/company_name/flag_summary.json
        """
        try:
            output_file = self.base_path / company / "flag_summary.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            self.logger.info(f"Saved results for {company}")
            
        except Exception as e:
            self.logger.error(f"Error saving results for {company}: {str(e)}")

def main():
    """
    Main execution function for citation flag counting and analysis.
    
    The function:
    1. Loads configuration from workflow_schema_cleaned.json
    2. Initializes FlagCounter instance
    3. Processes each company in the configuration
    4. Tracks success/failure statistics
    5. Prints processing summary
    
    Required files:
    - workflow_schema_cleaned.json
    - Data/company_name/flag_count.csv (for each company)
    - Data/company_name/company_name_cleaned.csv (for each company)
    
    Outputs:
    - Data/company_name/flag_summary.json (for each company)
    - logs/flag_counting.log
    """
    # Load schema
    schema_path = Path('workflow_schema_cleaned.json')
    if not schema_path.exists():
        raise FileNotFoundError("Cleaned schema file not found")
        
    # Initialize counter
    counter = FlagCounter(schema_path)
    
    # Process each company
    companies = counter.schema['config']['companies']
    
    # Setup progress tracking
    pbar = tqdm(companies, desc="Processing Companies", unit="company")
    stats = {'successful': [], 'failed': []}
    
    for company in pbar:
        pbar.set_description(f"Processing {company}")
        
        try:
            results = counter.process_company_flags(company)
            
            if results is not None:
                stats['successful'].append(company)
                pbar.set_postfix(status="Success")
            else:
                stats['failed'].append(company)
                pbar.set_postfix(status="Failed")
                
        except Exception as e:
            counter.logger.error(f"Failed to process {company}: {str(e)}")
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
