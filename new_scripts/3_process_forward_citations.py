import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from tqdm import tqdm
import scipy.sparse as sp


class ForwardCitationProcessor:
    """
    Processes forward citations following Section 2.2-2.3 specification 
    to populate V3 (forward citing patents) in G=(V1,V2,V3,E).
    
    The processor:
    1. Loads network structures from steps 1-2
    2. Validates temporal consistency of forward citations
    3. Constructs forward citing patent set V3
    4. Calculates temporal weights w_it
    """
    
    def __init__(self, base_path: Path = Path("Data")):
        self.base_path = base_path
        self.logger = self._setup_logger()
        self.alpha = 0.1  # Temporal decay parameter

    def _setup_logger(self) -> logging.Logger:
        """Configure logging."""
        logger = logging.getLogger('ForwardCitationProcessor')
        logger.setLevel(logging.INFO)
        
        Path("logs").mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/forward_citations.log')
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(handler)
        
        return logger

    def process_company_citations(self, company: str) -> Optional[Dict]:
        try:
            # Load network structures
            network_dir = self.base_path / company / "network"
            processed_dir = self.base_path / company / "processed"
            
            focal_patents = pd.read_parquet(network_dir / 'focal_patents.parquet')
            citation_edges = pd.read_parquet(network_dir / 'citation_edges.parquet')
            
            self.logger.info(f"Processing {company} forward citations:")
            self.logger.info(f"  Focal patents: {len(focal_patents)}")
            self.logger.info(f"  Citation edges: {len(citation_edges)}")
            
            # Identify forward citations
            forward_citations = citation_edges[
                citation_edges['cited_id'].isin(focal_patents['focal_patent'])
            ]
            
            # Calculate temporal weights using citation_date
            forward_citations['temporal_weight'] = self._calculate_temporal_weights(
                forward_citations['citation_date']
            )
            
            # Construct V3 set
            V3 = set(forward_citations['citing_id'].unique())
            
            # Calculate metrics
            metrics = self._calculate_citation_metrics(
                focal_patents, forward_citations
            )
            
            # Save processed data
            self._save_processed_data(
                company, forward_citations, V3, metrics
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error processing {company}: {str(e)}")
            return None

    def _calculate_temporal_weights(self, citation_dates: pd.Series) -> np.ndarray:
        """
        Calculates temporal weights following eq. (1):
        w_it = exp(-α(t - t0))
        
        Parameters
        ----------
        citation_dates : pd.Series
            Series of citation dates
            
        Returns
        -------
        np.ndarray
            Temporal weights w_it
        """
        # Convert to datetime if needed
        dates = pd.to_datetime(citation_dates)
        
        # Calculate time differences in years from earliest date
        t0 = dates.min()
        delta_t = (dates - t0).dt.days / 365.25
        
        return np.exp(-self.alpha * delta_t)

    def _calculate_citation_metrics(self,
                                 focal_patents: pd.DataFrame,
                                 forward_citations: pd.DataFrame) -> Dict:
        """
        Calculates forward citation metrics following Section 2.2.
        """
        n_focal = len(focal_patents)
        n_forward = len(forward_citations)
        n_citing = len(forward_citations['citing_id'].unique())
        
        # Calculate weighted citation counts
        weighted_citations = forward_citations.groupby('cited_id')['temporal_weight'].sum()
        
        return {
            'n_focal_patents': n_focal,
            'n_forward_citations': n_forward,
            'n_citing_patents': n_citing,
            'citations_per_patent': n_forward / n_focal if n_focal > 0 else 0,
            'weighted_citations_per_patent': weighted_citations.mean(),
            'network_density': n_forward / (n_focal * n_citing) 
                             if n_focal * n_citing > 0 else 0
        }
        
    def _save_processed_data(self,
                           company: str,
                           forward_citations: pd.DataFrame,
                           V3: Set[str],
                           metrics: Dict) -> None:
        """
        Persists processed forward citation data with temporal weights.
        """
        output_dir = self.base_path / company / "processed"
        output_dir.mkdir(exist_ok=True)
        
        # Save forward citations with weights
        forward_citations.to_parquet(
            output_dir / 'forward_citations.parquet'
        )
        
        # Save citing patents (V3)
        pd.DataFrame({'citing_patent': list(V3)}).to_parquet(
            output_dir / 'citing_patents.parquet'
        )
        
        # Save metrics
        pd.DataFrame([metrics]).to_json(
            output_dir / 'forward_citation_metrics.json'
        )

def main():
    """
    Executes forward citation processing pipeline.
    """
    processor = ForwardCitationProcessor()
    
    # Get companies
    companies = [d.name for d in processor.base_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')]
    
    # Process each company
    results = []
    for company in tqdm(companies, desc="Processing forward citations"):
        metrics = processor.process_company_citations(company)
        if metrics:
            metrics['company'] = company
            results.append(metrics)
    
    # Save summary statistics
    pd.DataFrame(results).to_csv(
        processor.base_path / 'forward_citation_summary.csv',
        index=False
    )

if __name__ == "__main__":
    main()