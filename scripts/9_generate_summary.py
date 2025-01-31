import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns

class SummaryGenerator:
    """
    Generate comprehensive summary reports and visualizations from patent analysis data.
    
    This class processes company-level Disruption Index (DI) and Pure F score data to create:
    1. Aggregate company performance metrics
    2. Time series analysis of innovation patterns
    3. Industry-wide comparisons and rankings
    4. Statistical visualizations
    
    The summary generation process combines multiple data sources:
    - Disruption Index (DI) data: Measures technological impact
    - Pure F scores: Measures citation matching quality
    - Patent counts and citation metrics
    
    Attributes:
        logger: Logging instance for tracking process and errors
        schema: Configuration schema loaded from JSON
        base_path: Base directory path for data files
        output_path: Directory for saving generated summaries and visualizations
    """
    
    def __init__(self, schema_path: Path):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/summary_generation.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load schema
        with open(schema_path) as f:
            self.schema = json.load(f)
        
        self.base_path = Path(self.schema['config']['base_path'])
        self.output_path = self.base_path / 'summary'
        self.output_path.mkdir(exist_ok=True)
        
    def generate_company_summary(self, company: str) -> Optional[Dict]:
        """
        Generate comprehensive summary metrics for a single company across all years.
        
        This method:
        1. Loads yearly DI and Pure F data
        2. Calculates aggregate metrics (totals and averages)
        3. Preserves yearly trends and patterns
        4. Combines multiple performance indicators
        
        Args:
            company (str): Name of the company to analyze
            
        Returns:
            Optional[Dict]: Summary dictionary with structure:
                {
                    'company_name': str,
                    'total_patents': int,
                    'total_citations': int,
                    'citations_per_patent': float,
                    'average_pure_f_score': float,
                    'average_disruption_index': float,
                    'yearly_metrics': {
                        'year': {
                            'disruption_index': float,
                            'pure_f_score': float,
                            'total_patents': int,
                            'total_citations': int
                        }
                    },
                    'processing_date': str
                }
            Returns None if processing fails
        
        The summary combines both point-in-time and trend analysis to provide
        a complete picture of the company's innovation performance.
        """
        try:
            # Load DI results
            di_file = self.base_path / company / "di_summary.json"
            if not di_file.exists():
                self.logger.error(f"DI summary file not found for {company}")
                return None
                
            with open(di_file) as f:
                di_data = json.load(f)
            
            # Calculate aggregate metrics across years
            yearly_data = di_data['yearly_di']
            
            # Aggregate metrics
            total_patents = sum(year_data['metrics']['total_patents'] for year_data in yearly_data.values())
            total_citations = sum(year_data['metrics']['total_citations'] for year_data in yearly_data.values())
            avg_di = np.mean([year_data['disruption_index'] for year_data in yearly_data.values()])
            avg_pure_f = np.mean([year_data['components']['pure_f_score'] for year_data in yearly_data.values()])
            
            summary = {
                'company_name': company,
                'total_patents': total_patents,
                'total_citations': total_citations,
                'citations_per_patent': total_citations / total_patents if total_patents > 0 else 0,
                'average_pure_f_score': float(avg_pure_f),
                'average_disruption_index': float(avg_di),
                'yearly_metrics': {
                    year: {
                        'disruption_index': data['disruption_index'],
                        'pure_f_score': data['components']['pure_f_score'],
                        'total_patents': data['metrics']['total_patents'],
                        'total_citations': data['metrics']['total_citations']
                    }
                    for year, data in yearly_data.items()
                },
                'processing_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary for {company}: {str(e)}")
            return None
            
    def generate_full_report(self):
        """
        Generate complete summary report with visualizations for all companies.
        
        This method:
        1. Processes each company's data
        2. Creates aggregate industry statistics
        3. Generates comparative rankings
        4. Produces visualization suite
        
        Outputs:
        1. CSV Files:
           - complete_summary.csv: Full dataset of all metrics
           - rankings_by_di.csv: Top 100 companies by Disruption Index
           - rankings_by_pure_f.csv: Top 100 companies by Pure F score
           - rankings_by_citations.csv: Top 100 companies by citation impact
        
        2. Visualizations:
           - di_distribution.png: Distribution of Disruption Index scores
           - pure_f_vs_di.png: Relationship between Pure F and DI
           - top_companies_di.png: Top 20 companies visualization
        
        3. Statistics:
           - summary_statistics.json: Industry-wide metrics and averages
        
        Returns:
            pd.DataFrame: Complete summary dataset, or None if processing fails
        """
        try:
            companies = self.schema['config']['companies']
            summaries = []
            
            # Process each company
            for company in tqdm(companies, desc="Generating Summaries"):
                summary = self.generate_company_summary(company)
                if summary:
                    summaries.append(summary)
            
            # Create summary DataFrame
            df = pd.DataFrame(summaries)
            
            # Save complete dataset
            df.to_csv(self.output_path / 'complete_summary.csv', index=False)
            
            # Explicitly call each generation function
            self.logger.info("Generating visualizations...")
            self._generate_visualizations(df)
            
            self.logger.info("Generating rankings...")
            self._generate_rankings(df)
            
            self.logger.info("Generating statistics...")
            self._generate_statistics(df)
            
            self.logger.info("Successfully generated complete summary report")
            return df
            
        except Exception as e:
            self.logger.error(f"Error generating full report: {str(e)}", exc_info=True)  # Added full traceback
            return None
            
    def _generate_visualizations(self, df: pd.DataFrame):
        """
        Generate suite of summary visualizations from company data.
        
        Creates three main visualization types:
        1. Distribution Analysis:
           - Histogram of Disruption Index scores
           - Shows industry-wide innovation patterns
           - Identifies outliers and clusters
        
        2. Correlation Analysis:
           - Pure F Score vs Disruption Index scatter plot
           - Reveals relationships between metrics
           - Highlights performance patterns
        
        3. Company Rankings:
           - Top 20 companies by Disruption Index
           - Visual comparison of leaders
           - Clear performance benchmarks
        
        Args:
            df (pd.DataFrame): Summary dataset with columns:
                - company_name
                - average_disruption_index
                - average_pure_f_score
                - total_patents
                - total_citations
        
        Outputs:
            Saves three PNG files to output_path:
            - di_distribution.png
            - pure_f_vs_di.png
            - top_companies_di.png
        """
        try:
            plt.style.use('seaborn')
            
            # Average DI Distribution
            plt.figure(figsize=(12, 6))
            sns.histplot(data=df, x='average_disruption_index', bins=30)
            plt.title('Distribution of Average Disruption Index')
            plt.savefig(self.output_path / 'di_distribution.png')
            plt.close()
            
            # Pure F vs DI
            plt.figure(figsize=(10, 10))
            sns.scatterplot(data=df, x='average_pure_f_score', y='average_disruption_index')
            plt.title('Average Pure F Score vs Average Disruption Index')
            plt.savefig(self.output_path / 'pure_f_vs_di.png')
            plt.close()
            
            # Top Companies by Average DI
            top_companies = df.nlargest(20, 'average_disruption_index')
            plt.figure(figsize=(15, 8))
            sns.barplot(data=top_companies, x='company_name', y='average_disruption_index')
            plt.xticks(rotation=45, ha='right')
            plt.title('Top 20 Companies by Average Disruption Index')
            plt.tight_layout()
            plt.savefig(self.output_path / 'top_companies_di.png')
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Error generating visualizations: {str(e)}", exc_info=True)
            
    def _generate_rankings(self, df: pd.DataFrame):
        """
        Generate multiple ranking lists based on different metrics.
        
        Creates three ranking categories:
        1. Disruption Index Rankings:
           - Measures overall innovation impact
           - Combines quality and quantity metrics
        
        2. Pure F Score Rankings:
           - Focuses on citation matching quality
           - Indicates research connection strength
        
        3. Citation Impact Rankings:
           - Based on citations per patent
           - Measures raw impact in the field
        
        Args:
            df (pd.DataFrame): Summary dataset with required metrics
        
        Outputs:
            Saves three CSV files to output_path:
            - rankings_by_di.csv: Top 100 by Disruption Index
            - rankings_by_pure_f.csv: Top 100 by Pure F score
            - rankings_by_citations.csv: Top 100 by citation impact
        """
        rankings = {
            'by_di': df.nlargest(100, 'disruption_index')[['company_name', 'disruption_index']],
            'by_pure_f': df.nlargest(100, 'pure_f_score')[['company_name', 'pure_f_score']],
            'by_citations': df.nlargest(100, 'citations_per_patent')[['company_name', 'citations_per_patent']]
        }
        
        for name, ranking in rankings.items():
            ranking.to_csv(self.output_path / f'rankings_{name}.csv', index=False)
            
    def _generate_statistics(self, df: pd.DataFrame):
        """
        Generate comprehensive statistical summary of the dataset.
        
        Calculates key industry statistics:
        1. Scale Metrics:
           - Total companies analyzed
           - Total patents in dataset
           - Total citations captured
        
        2. Central Tendencies:
           - Average and median Disruption Index
           - Average and median Pure F scores
           - Citation distribution metrics
        
        Args:
            df (pd.DataFrame): Summary dataset with all metrics
        
        Outputs:
            Saves summary_statistics.json with structure:
            {
                'total_companies': int,
                'total_patents': int,
                'total_citations': int,
                'average_di': float,
                'median_di': float,
                'average_pure_f': float,
                'median_pure_f': float,
                'generation_date': str
            }
        """
        stats = {
            'total_companies': len(df),
            'total_patents': df['total_patents'].sum(),
            'total_citations': df['total_citations'].sum(),
            'average_di': float(df['disruption_index'].mean()),
            'median_di': float(df['disruption_index'].median()),
            'average_pure_f': float(df['pure_f_score'].mean()),
            'median_pure_f': float(df['pure_f_score'].median()),
            'generation_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        with open(self.output_path / 'summary_statistics.json', 'w') as f:
            json.dump(stats, f, indent=2)

def main():
    """Main execution function"""
    # Load schema
    schema_path = Path('workflow_schema_cleaned.json')
    if not schema_path.exists():
        raise FileNotFoundError("Cleaned schema file not found")
        
    # Initialize generator
    generator = SummaryGenerator(schema_path)
    
    # Generate full report
    summary_df = generator.generate_full_report()
    
    if summary_df is not None:
        print("\nSummary Generation Complete")
        print("=" * 50)
        print(f"Total companies processed: {len(summary_df)}")
        print(f"Output directory: {generator.output_path}")
        print("\nGenerated files:")
        print("- complete_summary.csv")
        print("- rankings_by_di.csv")
        print("- rankings_by_pure_f.csv")
        print("- rankings_by_citations.csv")
        print("- summary_statistics.json")
        print("\nVisualizations:")
        print("- di_distribution.png")
        print("- pure_f_vs_di.png")
        print("- top_companies_di.png")
    else:
        print("\nError generating summary report")

if __name__ == "__main__":
    main()
