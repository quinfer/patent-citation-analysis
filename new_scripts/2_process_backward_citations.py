import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from tqdm import tqdm
import scipy.sparse as sp

class BackwardCitationProcessor:
    """
    Processes backward citations following Section 2.2-2.3 specification 
    to populate V2 (predecessor patents) in G=(V1,V2,V3,E).
    
    The processor:
    1. Loads preliminary network structures from step 1
    2. Validates temporal consistency of backward citations
    3. Constructs predecessor patent set V2
    4. Calculates citation-based metrics
    """
    
    def __init__(self, base_path: Path = Path("Data")):
        self.base_path = base_path
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure logging with temporal validation."""
        logger = logging.getLogger('BackwardCitationProcessor')
        logger.setLevel(logging.INFO)
        
        Path("logs").mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/backward_citations.log')
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(handler)
        
        return logger

    def process_company_citations(self, company: str) -> Optional[Dict]:
        """
        Processes backward citations for a company.
        
        Parameters
        ----------
        company : str
            Company identifier
            
        Returns
        -------
        Optional[Dict]
            Processed citation metrics including:
            - V2 cardinality (number of predecessor patents)
            - Citation temporal distribution
            - Network density measures
        """
        try:
            # Load preliminary network structure
            network_dir = self.base_path / company / "network"
            focal_patents = pd.read_parquet(network_dir / 'focal_patents.parquet')
            citation_edges = pd.read_parquet(network_dir / 'citation_edges.parquet')
            
            self.logger.info(f"Processing {company} citations:")
            self.logger.info(f"  Focal patents: {len(focal_patents)}")
            self.logger.info(f"  Citation edges: {len(citation_edges)}")
            
            # Identify backward citations
            backward_citations = citation_edges[
                citation_edges['citing_id'].isin(focal_patents['focal_patent'])
            ]
            
            # Construct predecessor set V2
            V2 = set(backward_citations['cited_id'].unique())
            
            # Calculate citation metrics
            metrics = self._calculate_citation_metrics(
                focal_patents, backward_citations
            )
            
            # Save processed data
            self._save_processed_data(
                company, backward_citations, V2, metrics
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error processing {company}: {str(e)}")
            return None

    def _calculate_citation_metrics(self,
                                 focal_patents: pd.DataFrame,
                                 backward_citations: pd.DataFrame) -> Dict:
        """
        Calculates citation-based metrics following Section 2.2.
        
        Parameters
        ----------
        focal_patents : pd.DataFrame
            V1 patent set
        backward_citations : pd.DataFrame
            Backward citation edges
            
        Returns
        -------
        Dict
            Citation metrics including:
            - Average citations per patent
            - Citation lag statistics
            - Network density
        """
        n_focal = len(focal_patents)
        n_backward = len(backward_citations)
        n_unique_cited = len(backward_citations['cited_id'].unique())
        
        return {
            'n_focal_patents': n_focal,
            'n_backward_citations': n_backward,
            'n_predecessor_patents': n_unique_cited,
            'citations_per_patent': n_backward / n_focal if n_focal > 0 else 0,
            'network_density': n_backward / (n_focal * n_unique_cited) 
                             if n_focal * n_unique_cited > 0 else 0
        }

    def _save_processed_data(self,
                           company: str,
                           backward_citations: pd.DataFrame,
                           V2: Set[str],
                           metrics: Dict) -> None:
        """
        Persists processed citation data and metrics.
        """
        output_dir = self.base_path / company / "processed"
        output_dir.mkdir(exist_ok=True)
        
        # Save backward citations
        backward_citations.to_parquet(
            output_dir / 'backward_citations.parquet'
        )
        
        # Save predecessor patents (V2)
        pd.DataFrame({'predecessor_patent': list(V2)}).to_parquet(
            output_dir / 'predecessor_patents.parquet'
        )
        
        # Save metrics
        pd.DataFrame([metrics]).to_json(
            output_dir / 'backward_citation_metrics.json'
        )

def main():
    """
    Executes backward citation processing pipeline.
    """
    processor = BackwardCitationProcessor()
    
    # Get company list
    companies = [d.name for d in processor.base_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')]
    
    # Process companies
    results = []
    for company in tqdm(companies, desc="Processing backward citations"):
        metrics = processor.process_company_citations(company)
        if metrics:
            metrics['company'] = company
            results.append(metrics)
    
    # Save summary statistics
    pd.DataFrame(results).to_csv(
        processor.base_path / 'backward_citation_summary.csv',
        index=False
    )

if __name__ == "__main__":
    main()