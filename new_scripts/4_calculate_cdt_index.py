import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from tqdm import tqdm
import scipy.sparse as sp

class CDtCalculator:
    """
    Implements CDt calculation and firm-level metrics following Section 2.3 
    and 3.3.3 of Funk & Owen-Smith (2017).
    
    Patent-level CDt:
    CDt = (1/nt) * Σ(-2fitbit + fit)/wit
    
    Firm-level metrics:
    1. CDmean5: Average CD5 index
    2. mCDscale5: CDmean5 × total impact
    3. CDtotal-5: Citations of negative CDt patents
    4. CDtotal+5: Citations of positive CDt patents
    """
    
    def __init__(self, base_path: Path = Path("Data")):
        self.base_path = base_path
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('CDtCalculator')
        logger.setLevel(logging.INFO)
        
        Path("logs").mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/cdt_calculation.log')
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(handler)
        
        return logger

    def calculate_company_cdt(self, company: str) -> Optional[Dict]:
        """
        Calculates patent-level CDt and firm-level aggregation metrics.
        """
        try:
            # Load processed citation data
            network_dir = self.base_path / company / "network"
            processed_dir = self.base_path / company / "processed"
            
            focal_patents = pd.read_parquet(network_dir / 'focal_patents.parquet')
            forward_citations = pd.read_parquet(processed_dir / 'forward_citations.parquet')
            backward_citations = pd.read_parquet(processed_dir / 'backward_citations.parquet')
            
            self.logger.info(f"Calculating CDt for {company}:")
            self.logger.info(f"  Focal patents: {len(focal_patents)}")
            self.logger.info(f"  Forward citations: {len(forward_citations)}")
            self.logger.info(f"  Backward citations: {len(backward_citations)}")
            
            # Calculate patent-level CDt
            cdt_scores = {}
            for patent_id in tqdm(focal_patents['focal_patent'], 
                                desc=f"Processing {company} patents"):
                cdt = self._calculate_patent_cdt(
                    patent_id,
                    forward_citations,
                    backward_citations
                )
                if cdt is not None:
                    cdt_scores[patent_id] = cdt
            
            # Calculate firm-level metrics
            metrics = self._calculate_firm_metrics(cdt_scores, forward_citations)
            
            # Log firm-level metrics
            self.logger.info(f"\nFirm-level metrics for {company}:")
            self.logger.info(f"  CDmean5: {metrics['cdmean5']:.3f}")
            self.logger.info(f"  mCDscale5: {metrics['mcdscale5']:.3f}")
            self.logger.info(f"  CDtotal-5: {metrics['cdtotal_neg']}")
            self.logger.info(f"  CDtotal+5: {metrics['cdtotal_pos']}")
            
            # Save results
            self._save_processed_data(company, cdt_scores, metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating CDt for {company}: {str(e)}")
            return None

    def _calculate_patent_cdt(self,
                            patent_id: str,
                            forward_citations: pd.DataFrame,
                            backward_citations: pd.DataFrame) -> Optional[float]:
        """
        Calculates CDt index for individual patent.
        """
        # Get forward citations
        patent_forwards = forward_citations[
            forward_citations['cited_id'] == patent_id
        ]
        
        nt = len(patent_forwards)
        if nt == 0:
            return None
            
        # Get backward citations
        patent_backwards = set(backward_citations[
            backward_citations['citing_id'] == patent_id
        ]['cited_id'])
        
        summation = 0
        for _, citation in patent_forwards.iterrows():
            # Forward citation indicator (fit)
            fit = 1
            
            # Backward citation indicator (bit)
            citing_backwards = set(backward_citations[
                backward_citations['citing_id'] == citation['citing_id']
            ]['cited_id'])
            bit = 1 if len(patent_backwards & citing_backwards) > 0 else 0
            
            # Get temporal weight
            wit = citation['temporal_weight']
            
            # Calculate contribution
            summation += (-2 * fit * bit + fit) / wit
            
        return summation / nt

    def _calculate_firm_metrics(self, 
                              cdt_scores: Dict[str, float],
                              forward_citations: pd.DataFrame) -> Dict:
        """
        Calculates firm-level CDt metrics following Section 3.3.3.
        """
        # Create DataFrame with CDt scores
        scores_df = pd.DataFrame([
            {'patent_id': p, 'cdt_score': s}
            for p, s in cdt_scores.items()
        ])
        
        # Calculate CDmean5 (average CDt)
        cdmean5 = scores_df['cdt_score'].mean()
        
        # Calculate total impact (I5total)
        total_impact = len(forward_citations)
        
        # Calculate mCDscale5 (CDmean5 × impact)
        mcdscale5 = cdmean5 * total_impact
        
        # Identify positive and negative CDt patents
        neg_patents = scores_df[scores_df['cdt_score'] < 0]['patent_id']
        pos_patents = scores_df[scores_df['cdt_score'] > 0]['patent_id']
        
        # Calculate CDtotal-5 and CDtotal+5
        cdtotal_neg = len(forward_citations[
            forward_citations['cited_id'].isin(neg_patents)
        ])
        cdtotal_pos = len(forward_citations[
            forward_citations['cited_id'].isin(pos_patents)
        ])
        
        return {
            # Primary firm-level metrics
            'cdmean5': float(cdmean5),
            'mcdscale5': float(mcdscale5),
            'cdtotal_neg': int(cdtotal_neg),
            'cdtotal_pos': int(cdtotal_pos),
            # Additional statistics
            'n_patents_with_cdt': len(scores_df),
            'median_cdt': float(scores_df['cdt_score'].median()),
            'std_cdt': float(scores_df['cdt_score'].std()),
            'min_cdt': float(scores_df['cdt_score'].min()),
            'max_cdt': float(scores_df['cdt_score'].max()),
            'destabilizing_ratio': float(len(pos_patents) / len(scores_df)),
            'consolidating_ratio': float(len(neg_patents) / len(scores_df))
        }

    def _save_processed_data(self,
                           company: str,
                           cdt_scores: Dict[str, float],
                           metrics: Dict) -> None:
        """
        Persists CDt scores and metrics.
        """
        output_dir = self.base_path / company / "processed"
        output_dir.mkdir(exist_ok=True)
        
        # Save patent-level scores
        pd.DataFrame([
            {'patent_id': p, 'cdt_score': s}
            for p, s in cdt_scores.items()
        ]).to_parquet(output_dir / 'patent_cdt_scores.parquet')
        
        # Save firm-level metrics
        pd.DataFrame([metrics]).to_json(
            output_dir / 'firm_cdt_metrics.json'
        )

def main():
    """
    Executes CDt calculation pipeline.
    """
    calculator = CDtCalculator()
    
    # Get companies
    companies = [d.name for d in calculator.base_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')]
    
    # Process companies
    results = []
    for company in tqdm(companies, desc="Calculating CDt scores"):
        metrics = calculator.calculate_company_cdt(company)
        if metrics:
            metrics['company'] = company
            results.append(metrics)
    
    # Save summary statistics
    if results:
        summary_df = pd.DataFrame(results)
        summary_df.to_csv(
            calculator.base_path / 'cdt_summary.csv',
            index=False
        )
        
        print("\nProcessing complete!")
        print(f"Processed {len(results)} companies")
        print("\nFirm-level CDt Statistics:")
        print(summary_df[['cdmean5', 'mcdscale5', 'cdtotal_neg', 'cdtotal_pos']].describe())

if __name__ == "__main__":
    main()