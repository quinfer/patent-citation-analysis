import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from tqdm import tqdm

class ForwardCitationMatcher:
    """
    A class to match and analyze forward citations for company patents.
    
    This class handles the process of:
    1. Loading company patent data and citation relationships
    2. Matching forward citations between different data sources
    3. Validating citation counts and temporal relationships
    4. Generating summary statistics for citation matching
    
    Attributes:
        logger: Logging instance for tracking process and errors
        schema: Configuration schema loaded from JSON
        base_path: Base directory path for data files
    """
    
    def __init__(self, schema_path: Path):
        """
        Initialize the ForwardCitationMatcher with configuration and logging setup.
        
        Args:
            schema_path (Path): Path to the JSON schema configuration file
            
        The initialization:
        1. Sets up logging to track process and errors
        2. Loads configuration schema
        3. Establishes base path for data files
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/forward_matching.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load schema
        with open(schema_path) as f:
            self.schema = json.load(f)
        
        self.base_path = Path(self.schema['config']['base_path'])
        
    def rematch_company_citations(self, company: str) -> Optional[pd.DataFrame]:
        """
        Rematch forward citations for a company using merged citation data.
        
        Args:
            company (str): Name of the company to process
            
        Returns:
            Optional[pd.DataFrame]: DataFrame containing citation matching results, or None if processing fails
            
        The function:
        1. Loads company's base patent data
        (containing original patent info and citation counts)
        2. Loads detailed citation relationship data
        3. Matches citations between the two sources
        4. Saves results to a CSV file
        5. Returns the matched data as a DataFrame
        
        The output DataFrame contains:
        - patent_id: Unique identifier for each patent
        - grant_year: Year the patent was granted
        - total_forward_citations: Total number of forward citations
        - matched_citations: Number of citations verified in detailed data
        - company_name: Name of the company
        - processing_date: Date of processing
        - match_rate: Percentage of citations that were verified
        """
        try:
            # Load the company's base patent data
            company_patents_file = self.base_path / company / f"{company}_cleaned.csv"
            if not company_patents_file.exists():
                self.logger.error(f"Base patent data file not found for {company}")
                return None
                
            company_patents_df = pd.read_csv(company_patents_file, dtype={'citing_patent_id': str})
            
            # Load the detailed citation relationships data
            citation_links_file = self.base_path / company / "merged_cleaned_data.csv"
            if not citation_links_file.exists():
                self.logger.error(f"Citation relationships file not found for {company}")
                return None
                
            citation_links_df = pd.read_csv(citation_links_file, dtype={'focal_patent': str, 'connected_patent': str})
            
            # Match citations and generate summary
            matched_df = self._match_citations(company_patents_df, citation_links_df, company)
            
            # Save the citation matching summary
            output_file = self.base_path / company / "flag_count.csv"
            matched_df.to_csv(output_file, index=False)
            
            self.logger.info(f"Completed forward citation matching for {company}")
            return matched_df
            
        except Exception as e:
            self.logger.error(f"Error matching citations for {company}: {str(e)}")
            return None
            
    def _match_citations(self, company_patents_df: pd.DataFrame, citation_links_df: pd.DataFrame, company: str) -> pd.DataFrame:
        """
        Match and analyze forward citations between company patents and citation relationships.
        
        Args:
            company_patents_df (pd.DataFrame): DataFrame containing the company's patents and their metadata
                Required columns: citing_patent_id, granted_date, forward_citation_count
            citation_links_df (pd.DataFrame): DataFrame containing all citation relationships
                Required columns: focal_patent, connected_patent, citation_date, citation_type
            company (str): Name of the company being processed
            
        Returns:
            pd.DataFrame: DataFrame containing citation matching results
            
        The function performs these steps:
        1. Adds year information to both datasets
        2. Filters for forward citations only
        3. For each patent:
           - Counts total citations from original data
           - Counts matched citations from detailed data
           - Validates citation counts
           - Calculates match rate
        4. Returns compiled results as DataFrame
        
        Note:
        - Only counts citations up to the patent's grant year
        - Handles cases where matched citations exceed total citations
        - Sets match rate to 0 for patents with no citations
        """
        try:
            self.logger.info(f"{company}: Starting matching process with {len(company_patents_df)} patents")
            
            # Add year information to both datasets
            company_patents_df['patent_grant_year'] = pd.to_datetime(company_patents_df['granted_date']).dt.year
            citation_links_df['citation_year'] = pd.to_datetime(citation_links_df['citation_date']).dt.year
            
            # Filter to only include forward citations
            forward_citations = citation_links_df[citation_links_df['citation_type'] == 'forward']
            
            results = []
            # Process each patent
            for _, patent_row in tqdm(company_patents_df.iterrows(), desc=f"{company} - Processing patents"):
                patent_id = patent_row['citing_patent_id']
                patent_grant_year = patent_row['patent_grant_year']
                
                # Count citations up to the patent's grant year
                total_citations = patent_row['forward_citation_count']
                matched_citations = len(forward_citations[
                    (forward_citations['focal_patent'] == patent_id) & 
                    (forward_citations['citation_year'] <= patent_grant_year)
                ])
                
                # Validate citation counts
                if matched_citations > total_citations:
                    self.logger.warning(
                        f"Found more citations than originally recorded for patent {patent_id}:\n"
                        f"Original count: {total_citations}, Found citations: {matched_citations}\n"
                        f"Using the higher number for accuracy."
                    )
                    total_citations = max(total_citations, matched_citations)
                
                # Compile results
                result = {
                    'patent_id': patent_id,
                    'grant_year': patent_grant_year,
                    'total_forward_citations': total_citations,
                    'matched_citations': matched_citations,
                    'company_name': company,
                    'processing_date': datetime.now().strftime('%Y-%m-%d')
                }
                
                # Calculate match rate
                result['match_rate'] = (result['matched_citations'] / result['total_forward_citations'] 
                                      if result['total_forward_citations'] > 0 else 0)
                
                results.append(result)
            
            return pd.DataFrame(results)
            
        except Exception as e:
            self.logger.error(f"{company}: Error in matching process: {str(e)}")
            raise

def main():
    """
    Main execution function for the forward citation matching process.
    
    This function:
    1. Loads the configuration schema
    2. Initializes the ForwardCitationMatcher
    3. Processes each company in the configuration
    4. Tracks success/failure statistics
    5. Prints a summary of the processing results
    
    The function uses tqdm for progress tracking and handles exceptions
    for each company independently to prevent total process failure.
    """
    # Load schema
    schema_path = Path('workflow_schema_cleaned.json')
    if not schema_path.exists():
        raise FileNotFoundError("Cleaned schema file not found")
        
    # Initialize matcher
    matcher = ForwardCitationMatcher(schema_path)
    
    # Process each company
    companies = matcher.schema['config']['companies']
    
    # Setup progress tracking
    pbar = tqdm(companies, desc="Matching Forward Citations", unit="company")
    stats = {'successful': [], 'failed': []}
    
    for company in pbar:
        pbar.set_description(f"Processing {company}")
        
        try:
            matched_df = matcher.rematch_company_citations(company)
            
            if matched_df is not None:
                stats['successful'].append(company)
                pbar.set_postfix(status="Success")
            else:
                stats['failed'].append(company)
                pbar.set_postfix(status="Failed")
                
        except Exception as e:
            matcher.logger.error(f"Failed to match {company}: {str(e)}")
            stats['failed'].append(company)
            pbar.set_postfix(status="Error")
            continue
    
    # Print summary
    print("\nMatching Summary")
    print("=" * 50)
    print(f"Successfully matched: {len(stats['successful'])} companies")
    print(f"Failed to match: {len(stats['failed'])} companies")
    
    if stats['failed']:
        print("\nFailed companies:")
        for company in stats['failed']:
            print(f"- {company}")

if __name__ == "__main__":
    main()
