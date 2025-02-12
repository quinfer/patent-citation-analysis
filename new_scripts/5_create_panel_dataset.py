import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from tqdm import tqdm

class PanelConstructor:
    """
    Constructs firm-year panel dataset from CDt calculations following 
    Section 3.3.3 of Funk & Owen-Smith (2017).
    """
    
    def __init__(self, base_path: Path = Path("Data")):
        self.base_path = base_path
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('PanelConstructor')
        logger.setLevel(logging.INFO)
        
        Path("logs").mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/panel_construction.log')
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(handler)
        
        return logger

    def create_panel_dataset(self) -> pd.DataFrame:
        """
        Creates firm-year panel from processed CDt results.
        """
        panel_data = []
        
        # Process each company
        companies = [d for d in self.base_path.iterdir() 
                    if d.is_dir() and not d.name.startswith('.')]
        
        for company in tqdm(companies, desc="Creating panel dataset"):
            try:
                # Load CDt and citation data
                cdt_path = company / "processed" / 'patent_cdt_scores.parquet'
                forward_path = company / "processed" / 'forward_citations.parquet'
                
                if not cdt_path.exists() or not forward_path.exists():
                    self.logger.warning(f"Missing data for {company.name}")
                    continue
                    
                patent_scores = pd.read_parquet(cdt_path)
                forward_citations = pd.read_parquet(forward_path)
                
                # Extract years from citation dates
                forward_citations['year'] = pd.to_datetime(
                    forward_citations['citation_date']
                ).dt.year
                
                # Calculate yearly metrics
                for year in forward_citations['year'].unique():
                    # Get relevant patents and citations for year
                    year_citations = forward_citations[
                        forward_citations['year'] == year
                    ]
                    
                    year_patents = patent_scores[
                        patent_scores['patent_id'].isin(year_citations['cited_id'])
                    ]
                    
                    if len(year_patents) == 0:
                        continue
                    
                    # Calculate yearly metrics
                    cdmean5 = year_patents['cdt_score'].mean()
                    total_impact = len(year_citations)
                    mcdscale5 = cdmean5 * total_impact
                    
                    # Calculate CDtotal metrics
                    neg_patents = year_patents[year_patents['cdt_score'] < 0]['patent_id']
                    pos_patents = year_patents[year_patents['cdt_score'] > 0]['patent_id']
                    
                    cdtotal_neg = len(year_citations[
                        year_citations['cited_id'].isin(neg_patents)
                    ])
                    cdtotal_pos = len(year_citations[
                        year_citations['cited_id'].isin(pos_patents)
                    ])
                    
                    # Create panel row
                    panel_data.append({
                        'firm': company.name,
                        'year': year,
                        'cdmean5': cdmean5,
                        'mcdscale5': mcdscale5,
                        'cdtotal_neg': cdtotal_neg,
                        'cdtotal_pos': cdtotal_pos,
                        'n_patents': len(year_patents),
                        'n_citations': total_impact,
                        'n_neg_patents': len(neg_patents),
                        'n_pos_patents': len(pos_patents)
                    })
                    
            except Exception as e:
                self.logger.error(f"Error processing {company.name}: {str(e)}")
                continue
        
        # Create and save panel dataset
        panel_df = pd.DataFrame(panel_data)
        panel_df = panel_df.sort_values(['firm', 'year'])
        
        # Save outputs
        panel_df.to_csv(self.base_path / 'firm_year_panel.csv', index=False)
        panel_df.to_parquet(self.base_path / 'firm_year_panel.parquet')
        
        # Log summary statistics
        self.logger.info("\nPanel Dataset Summary:")
        self.logger.info(f"Number of firms: {panel_df['firm'].nunique()}")
        self.logger.info(f"Year range: {panel_df['year'].min()}-{panel_df['year'].max()}")
        self.logger.info(f"Total observations: {len(panel_df)}")
        
        return panel_df

    def generate_summary_statistics(self, panel_df: pd.DataFrame) -> None:
        """
        Generates detailed summary statistics for panel dataset.
        """
        # Create summary directory
        summary_dir = self.base_path / 'summary'
        summary_dir.mkdir(exist_ok=True)
        
        # Overall statistics
        desc_stats = panel_df.describe()
        desc_stats.to_csv(summary_dir / 'panel_summary_stats.csv')
        
        # Firm-level averages
        firm_stats = panel_df.groupby('firm').agg({
            'cdmean5': 'mean',
            'mcdscale5': 'mean',
            'cdtotal_neg': 'sum',
            'cdtotal_pos': 'sum',
            'n_patents': 'sum',
            'n_citations': 'sum'
        }).reset_index()
        firm_stats.to_csv(summary_dir / 'firm_level_averages.csv', index=False)
        
        # Year-level averages
        year_stats = panel_df.groupby('year').agg({
            'cdmean5': 'mean',
            'mcdscale5': 'mean',
            'cdtotal_neg': 'sum',
            'cdtotal_pos': 'sum',
            'n_patents': 'sum',
            'n_citations': 'sum'
        }).reset_index()
        year_stats.to_csv(summary_dir / 'year_level_averages.csv', index=False)

def main():
    """
    Creates firm-year panel dataset from CDt results.
    """
    constructor = PanelConstructor()
    
    print("Creating panel dataset...")
    panel_df = constructor.create_panel_dataset()
    
    print("\nGenerating summary statistics...")
    constructor.generate_summary_statistics(panel_df)
    
    print("\nPanel dataset creation complete!")
    print(f"Total firms: {panel_df['firm'].nunique()}")
    print(f"Year range: {panel_df['year'].min()}-{panel_df['year'].max()}")
    print(f"Total observations: {len(panel_df)}")

if __name__ == "__main__":
    main()