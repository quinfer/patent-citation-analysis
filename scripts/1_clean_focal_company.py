import pandas as pd
import logging
import json
from pathlib import Path
from typing import Union, Dict, Optional, List, Tuple
from jsonschema import validate
from datetime import datetime
import numpy as np
from dataclasses import dataclass
from tqdm import tqdm
import time

@dataclass
class DataQualityMetrics:
    """Class to hold data quality metrics"""
    total_rows: int
    null_counts: Dict[str, int]
    duplicate_rows: int
    invalid_dates: Dict[str, int]
    invalid_numbers: Dict[str, int]
    unique_values: Dict[str, int]
    data_ranges: Dict[str, Tuple]
    outliers: Dict[str, List]

class DataQualityReport:
    """Class to generate and manage data quality reports"""
    
    def __init__(self, company_name: str):
        self.company_name = company_name
        self.timestamp = datetime.now()
        self.metrics: Optional[DataQualityMetrics] = None
        self.report_path = Path('reports') / 'data_quality'
        self.report_path.mkdir(parents=True, exist_ok=True)

    def calculate_metrics(self, df: pd.DataFrame) -> DataQualityMetrics:
        """Calculate data quality metrics for a DataFrame"""
        
        # Basic metrics
        total_rows = len(df)
        null_counts = df.isnull().sum().to_dict()
        duplicate_rows = df.duplicated().sum()
        
        # Date validation
        date_columns = ['application_date', 'grant_date']
        invalid_dates = {}
        for col in date_columns:
            if col in df.columns:
                try:
                    invalid_dates[col] = pd.to_datetime(
                        df[col], errors='coerce'
                    ).isnull().sum()
                except Exception:
                    invalid_dates[col] = len(df)

        # Numeric validation
        numeric_columns = ['forward_citation_count']
        invalid_numbers = {}
        outliers = {}
        data_ranges = {}
        
        for col in numeric_columns:
            if col in df.columns:
                # Convert to numeric, counting invalid values
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                invalid_numbers[col] = numeric_series.isnull().sum()
                
                # Calculate outliers using IQR method
                Q1 = numeric_series.quantile(0.25)
                Q3 = numeric_series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers[col] = df[
                    (numeric_series < lower_bound) | 
                    (numeric_series > upper_bound)
                ][col].tolist()
                
                # Calculate range
                data_ranges[col] = (
                    numeric_series.min(),
                    numeric_series.max()
                )

        # Unique values for categorical columns
        categorical_columns = ['citing_patent_id']
        unique_values = {
            col: df[col].nunique() 
            for col in categorical_columns 
            if col in df.columns
        }

        return DataQualityMetrics(
            total_rows=total_rows,
            null_counts=null_counts,
            duplicate_rows=duplicate_rows,
            invalid_dates=invalid_dates,
            invalid_numbers=invalid_numbers,
            unique_values=unique_values,
            data_ranges=data_ranges,
            outliers=outliers
        )

    def generate_report(self, df: pd.DataFrame) -> str:
        """Generate a detailed data quality report"""
        self.metrics = self.calculate_metrics(df)
        
        report = []
        report.append(f"Data Quality Report for {self.company_name}")
        report.append(f"Generated on: {self.timestamp}")
        report.append("-" * 50)
        
        # Basic Statistics
        report.append("\n1. Basic Statistics:")
        report.append(f"Total Rows: {self.metrics.total_rows}")
        report.append(f"Duplicate Rows: {self.metrics.duplicate_rows}")
        report.append(f"Duplicate Rate: {(self.metrics.duplicate_rows/self.metrics.total_rows)*100:.2f}%")
        
        # Null Values
        report.append("\n2. Null Values:")
        for col, null_count in self.metrics.null_counts.items():
            null_rate = (null_count/self.metrics.total_rows)*100
            report.append(f"{col}: {null_count} ({null_rate:.2f}%)")
        
        # Invalid Dates
        report.append("\n3. Invalid Dates:")
        for col, invalid_count in self.metrics.invalid_dates.items():
            invalid_rate = (invalid_count/self.metrics.total_rows)*100
            report.append(f"{col}: {invalid_count} ({invalid_rate:.2f}%)")
        
        # Invalid Numbers
        report.append("\n4. Invalid Numbers:")
        for col, invalid_count in self.metrics.invalid_numbers.items():
            invalid_rate = (invalid_count/self.metrics.total_rows)*100
            report.append(f"{col}: {invalid_count} ({invalid_rate:.2f}%)")
        
        # Data Ranges
        report.append("\n5. Data Ranges:")
        for col, (min_val, max_val) in self.metrics.data_ranges.items():
            report.append(f"{col}: {min_val} to {max_val}")
        
        # Outliers
        report.append("\n6. Outliers:")
        for col, outlier_values in self.metrics.outliers.items():
            outlier_count = len(outlier_values)
            outlier_rate = (outlier_count/self.metrics.total_rows)*100
            report.append(f"{col}: {outlier_count} outliers ({outlier_rate:.2f}%)")
            if outlier_values:
                report.append(f"Sample outliers: {outlier_values[:5]}")
        
        # Unique Values
        report.append("\n7. Unique Values:")
        for col, unique_count in self.metrics.unique_values.items():
            unique_rate = (unique_count/self.metrics.total_rows)*100
            report.append(f"{col}: {unique_count} ({unique_rate:.2f}%)")
        
        return "\n".join(report)

    def save_report(self, report_text: str) -> Path:
        """Save the report to a file"""
        timestamp = self.timestamp.strftime("%Y%m%d_%H%M%S")
        report_file = self.report_path / f"{self.company_name}_quality_report_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        return report_file

class FocalCompanyCleaner:
    """Class to handle cleaning of focal company data"""
    
    # Define expected schema for validation
    EXPECTED_COLUMNS = {
        'required': [
            'citing_patent_id',
            'forward_citation_count',
            'forward_cited_numbers',
            'forward_cited_dates',
            'backward_cited_numbers',
            'backward_cited_dates',
            'grant_date',
            'ipc_code'
        ],
        'optional': [
            'application_date',
            'assignee_name',
            'other_metadata'
        ]
    }
    
    def __init__(self, schema_path: Union[str, Path]):
        """
        Initialize the cleaner with workflow schema
        
        Args:
            schema_path (Union[str, Path]): Path to the cleaned workflow schema
        """
        self.schema = self._load_schema(schema_path)
        self.base_path = Path(self.schema['config']['base_path'])
        self.logger = self._setup_logger()

    def _load_schema(self, schema_path: Union[str, Path]) -> Dict:
        """Load and validate the workflow schema"""
        with open(schema_path, 'r') as f:
            schema = json.load(f)
            
        # Validate schema structure
        required_keys = {'config', 'required_folders', 'expected_files', 'workflow_steps'}
        if not all(key in schema for key in required_keys):
            raise ValueError(f"Schema missing required keys: {required_keys}")
            
        return schema

    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('FocalCompanyCleaner')
        logger.setLevel(logging.INFO)
        
        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(log_dir / 'focal_company_cleaning.log')
        
        # Create formatters and add it to handlers
        log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(log_format)
        f_handler.setFormatter(log_format)
        
        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)
        
        return logger

    def validate_company_file(self, df: pd.DataFrame, company_name: str) -> bool:
        """
        Validate the company DataFrame against expected schema
        
        Args:
            df (pd.DataFrame): Company DataFrame to validate
            company_name (str): Name of the company for logging
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        # Check required columns
        missing_cols = set(self.EXPECTED_COLUMNS['required']) - set(df.columns)
        if missing_cols:
            self.logger.error(f"Company {company_name} missing required columns: {missing_cols}")
            return False
            
        # Validate data types
        try:
            # Verify citing_patent_id is string
            df['citing_patent_id'] = df['citing_patent_id'].astype(str)
            
            # Verify forward_citation_count is numeric
            df['forward_citation_count'] = pd.to_numeric(df['forward_citation_count'], errors='raise')
            
        except Exception as e:
            self.logger.error(f"Data type validation failed for {company_name}: {str(e)}")
            return False
            
        return True

    def clean_company_data(self, company_name: str) -> Optional[pd.DataFrame]:
        """Clean the focal company data for a specific company"""
        try:
            # Construct file paths
            company_folder = self.base_path / company_name
            input_file = company_folder / f"{company_name}.csv"
            
            self.logger.info(f"Starting processing for {company_name}")
            self.logger.info(f"Reading file: {input_file}")
            
            # Try reading with different delimiters
            try:
                df = pd.read_csv(
                    input_file,
                    delimiter=';',
                    dtype={'citing_patent_id': str},
                    encoding='utf-8-sig',
                    on_bad_lines='skip',
                    low_memory=False
                )
                # Check if we got a single column (indicating wrong delimiter)
                if len(df.columns) == 1:
                    self.logger.info(f"{company_name}: Retrying with comma delimiter")
                    df = pd.read_csv(
                        input_file,
                        delimiter=',',
                        dtype={'citing_patent_id': str},
                        encoding='utf-8-sig',
                        on_bad_lines='skip',
                        low_memory=False
                    )
            except Exception as e:
                self.logger.error(f"{company_name}: Error reading CSV: {str(e)}")
                raise
            
            self.logger.info(f"{company_name}: Successfully read CSV with {len(df)} rows")
            self.logger.info(f"{company_name} columns: {df.columns.tolist()}")
            self.logger.info(f"{company_name} dtypes:\n{df.dtypes}")
            
            # Validate required columns
            required_columns = {'citing_patent_id', 'forward_cited_numbers', 'forward_citation_count'}
            missing_columns = required_columns - set(df.columns)
            if missing_columns:
                self.logger.error(f"Company {company_name} missing required columns: {missing_columns}")
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Clean the data
            df = self._clean_dataframe(df)
            
            # Save cleaned data
            self._save_cleaned_data(df, company_folder, company_name)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to process {company_name}: {str(e)}")
            self.logger.error(f"Full error traceback for {company_name}:", exc_info=True)
            return None

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the DataFrame with detailed error handling"""
        try:
            df = df.copy()
            
            # Clean column names
            df.columns = df.columns.str.replace('ï»¿', '').str.strip()
            
            # Log column cleaning
            self.logger.info(f"Cleaned columns: {df.columns.tolist()}")
            
            # Remove rows with null citing_patent_id
            initial_rows = len(df)
            df = df.dropna(subset=['citing_patent_id'])
            rows_dropped = initial_rows - len(df)
            self.logger.info(f"Dropped {rows_dropped} rows with null citing_patent_id")
            
            # Clean string columns
            string_columns = df.select_dtypes(include=['object']).columns
            for col in string_columns:
                try:
                    df[col] = df[col].str.strip()
                    self.logger.info(f"Cleaned string column: {col}")
                except Exception as e:
                    self.logger.error(f"Error cleaning string column {col}: {str(e)}")
                    raise
            
            # Handle forward_cited_numbers with detailed logging
            if 'forward_cited_numbers' in df.columns:
                try:
                    df['forward_cited_numbers'] = df['forward_cited_numbers'].apply(
                        lambda x: ', '.join(str(x).split(', ')) if pd.notnull(x) else ''
                    )
                    self.logger.info("Successfully cleaned forward_cited_numbers")
                except Exception as e:
                    self.logger.error(f"Error cleaning forward_cited_numbers: {str(e)}")
                    self.logger.error(f"Sample of forward_cited_numbers:\n{df['forward_cited_numbers'].head()}")
                    raise
            
            # Add new cleaning steps for citation analysis
            if 'forward_cited_dates' in df.columns:
                df['forward_cited_dates'] = df['forward_cited_dates'].apply(
                    lambda x: ', '.join(str(x).split(', ')) if pd.notnull(x) else ''
                )
            
            if 'backward_cited_numbers' in df.columns:
                df['backward_cited_numbers'] = df['backward_cited_numbers'].apply(
                    lambda x: ', '.join(str(x).split(', ')) if pd.notnull(x) else ''
                )
            
            if 'backward_cited_dates' in df.columns:
                df['backward_cited_dates'] = df['backward_cited_dates'].apply(
                    lambda x: ', '.join(str(x).split(', ')) if pd.notnull(x) else ''
                )

            # Clean and standardize IPC codes
            if 'ipc_code' in df.columns:
                df['ipc_code'] = df['ipc_code'].str.extract(r'([A-H]\d+[A-Z]\d+)', expand=False)
                df['ipc_section'] = df['ipc_code'].str[0]  # Extract section (A-H)

            # Convert dates to datetime
            date_columns = ['grant_date', 'application_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # Add citation count validation
            if 'forward_citation_count' in df.columns:
                # Verify forward_citation_count matches actual citations
                df['actual_forward_count'] = df['forward_cited_numbers'].str.count(',') + 1
                df.loc[df['forward_cited_numbers'] == '', 'actual_forward_count'] = 0
                
                # Log discrepancies
                discrepancies = (df['forward_citation_count'] != df['actual_forward_count'])
                if discrepancies.any():
                    self.logger.warning(
                        f"Found {discrepancies.sum()} rows with citation count discrepancies"
                    )
                    
                # Use actual count
                df['forward_citation_count'] = df['actual_forward_count']
                df.drop('actual_forward_count', axis=1, inplace=True)

            return df
            
        except Exception as e:
            self.logger.error(f"Error in _clean_dataframe: {str(e)}")
            self.logger.error("DataFrame state at error:", exc_info=True)
            raise

    def _save_cleaned_data(self, df: pd.DataFrame, company_folder: Path, company_name: str) -> None:
        """
        Save the cleaned DataFrame
        
        Args:
            df (pd.DataFrame): Cleaned DataFrame
            company_folder (Path): Path to company folder
            company_name (str): Name of the company
        """
        output_file = company_folder / f"{company_name}_cleaned.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        self.logger.info(f"Saved cleaned data to: {output_file}")

class ConsolidatedQualityReport:
    """Class to generate consolidated quality reports across all companies"""
    
    def __init__(self):
        self.report_path = Path('reports') / 'data_quality'
        self.report_path.mkdir(parents=True, exist_ok=True)
        self.companies_metrics: Dict[str, Dict[str, DataQualityMetrics]] = {}
        self.timestamp = datetime.now()

    def add_company_metrics(self, company_name: str, 
                          original_metrics: DataQualityMetrics, 
                          cleaned_metrics: DataQualityMetrics):
        """Add a company's metrics to the consolidated report"""
        self.companies_metrics[company_name] = {
            'original': original_metrics,
            'cleaned': cleaned_metrics
        }

    def generate_consolidated_report(self) -> str:
        """Generate a consolidated report across all companies"""
        if not self.companies_metrics:
            raise ValueError("No company metrics available. Process some companies first.")
        
        report = []
        report.append("Consolidated Data Quality Report")
        report.append(f"Generated on: {self.timestamp}")
        report.append(f"Total Companies Processed: {len(self.companies_metrics)}")
        report.append("=" * 80)

        # Summary statistics across all companies
        total_rows_original = sum(m['original'].total_rows for m in self.companies_metrics.values())
        total_rows_cleaned = sum(m['cleaned'].total_rows for m in self.companies_metrics.values())
        
        report.append("\n1. Overall Statistics:")
        report.append(f"Total Rows (Original): {total_rows_original:,}")
        report.append(f"Total Rows (Cleaned): {total_rows_cleaned:,}")
        report.append(f"Row Reduction: {((total_rows_original - total_rows_cleaned)/total_rows_original)*100:.2f}%")

        # Company-by-company summary
        report.append("\n2. Company-by-Company Summary:")
        for company, metrics in self.companies_metrics.items():
            report.append(f"\n{company}:")
            report.append("-" * 40)
            
            # Basic metrics
            report.append("Rows:")
            report.append(f"  Original: {metrics['original'].total_rows:,}")
            report.append(f"  Cleaned: {metrics['cleaned'].total_rows:,}")
            report.append(f"  Reduction: {((metrics['original'].total_rows - metrics['cleaned'].total_rows)/metrics['original'].total_rows)*100:.2f}%")
            
            # Null values
            report.append("\nNull Values (Original → Cleaned):")
            for col in metrics['original'].null_counts.keys():
                orig_nulls = metrics['original'].null_counts.get(col, 0)
                clean_nulls = metrics['cleaned'].null_counts.get(col, 0)
                report.append(f"  {col}: {orig_nulls:,} → {clean_nulls:,}")

        # Cross-company analysis
        report.append("\n3. Cross-Company Analysis:")
        
        # Data volume distribution
        data_volumes = [(company, metrics['cleaned'].total_rows) 
                       for company, metrics in self.companies_metrics.items()]
        data_volumes.sort(key=lambda x: x[1], reverse=True)
        
        report.append("\nData Volume Distribution (Top 5):")
        for company, volume in data_volumes[:5]:
            report.append(f"  {company}: {volume:,} rows")

        # Quality metrics
        report.append("\nQuality Metrics (Average across companies):")
        avg_duplicate_rate = np.mean([
            m['cleaned'].duplicate_rows/m['cleaned'].total_rows 
            for m in self.companies_metrics.values()
        ]) * 100
        report.append(f"Average Duplicate Rate: {avg_duplicate_rate:.2f}%")

        return "\n".join(report)

    def save_consolidated_report(self, report_text: str) -> Path:
        """Save the consolidated report"""
        timestamp = self.timestamp.strftime("%Y%m%d_%H%M%S")
        report_file = self.report_path / f"consolidated_quality_report_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        return report_file

class ProcessingStats:
    """Class to track processing statistics"""
    def __init__(self):
        self.total_companies = 0
        self.successful = []
        self.failed = []
        self.skipped = []
        self.start_time = time.time()
    
    def get_summary(self) -> Dict[str, any]:
        """Get processing summary"""
        elapsed_time = time.time() - self.start_time
        return {
            'total': self.total_companies,
            'successful': len(self.successful),
            'failed': len(self.failed),
            'skipped': len(self.skipped),
            'elapsed_time': elapsed_time,
            'success_rate': (len(self.successful) / self.total_companies * 100 
                           if self.total_companies > 0 else 0)
        }
    
    def print_detailed_report(self):
        """Print detailed processing report"""
        summary = self.get_summary()
        
        print("\n" + "="*50)
        print("Processing Summary")
        print("="*50)
        print(f"Total Companies: {summary['total']}")
        print(f"Successfully Processed: {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {len(self.failed)}")
        print(f"Skipped: {len(self.skipped)}")
        print(f"Total Time: {summary['elapsed_time']:.1f} seconds")
        
        if self.failed:
            print("\nFailed Companies:")
            for company, error in self.failed:
                print(f"- {company}: {error}")
        
        if self.skipped:
            print("\nSkipped Companies:")
            for company, reason in self.skipped:
                print(f"- {company}: {reason}")

def main():
    """Main execution function"""
    # Load schema - changed from workflow_schema_cleaned.json to workflow_schema.json
    schema_path = Path('workflow_schema.json')
    if not schema_path.exists():
        raise FileNotFoundError("Schema file not found: workflow_schema.json")
    
    # Initialize cleaner and consolidated report
    cleaner = FocalCompanyCleaner(schema_path)
    consolidated_report = ConsolidatedQualityReport()
    
    # Initialize processing stats
    stats = ProcessingStats()
    companies = cleaner.schema['config']['companies']
    stats.total_companies = len(companies)
    
    # Setup progress bar
    pbar = tqdm(companies, desc="Processing Companies", 
                unit="company", ncols=100)
    
    # Process each company
    for company in pbar:
        try:
            # Update progress bar description
            pbar.set_description(f"Processing {company}")
            
            # Load original data first
            company_folder = Path(cleaner.base_path) / company
            input_file = company_folder / f"{company}.csv"
            
            if not input_file.exists():
                stats.skipped.append((company, "File not found"))
                pbar.set_postfix(status="Skipped")
                continue
            
            # Read and analyze original data
            original_df = pd.read_csv(
                input_file,
                delimiter=';',
                dtype={'citing_patent_id': str},
                encoding='utf-8-sig',
                on_bad_lines='skip',
                low_memory=False
            )
            
            # Generate quality report for original data
            quality_reporter_original = DataQualityReport(company)
            original_metrics = quality_reporter_original.calculate_metrics(original_df)
            original_report = quality_reporter_original.generate_report(original_df)
            quality_reporter_original.save_report(original_report)
            
            # Clean the data
            cleaned_df = cleaner.clean_company_data(company)
            
            if cleaned_df is not None:
                # Generate quality report for cleaned data
                quality_reporter_cleaned = DataQualityReport(f"{company}_cleaned")
                cleaned_metrics = quality_reporter_cleaned.calculate_metrics(cleaned_df)
                cleaned_report = quality_reporter_cleaned.generate_report(cleaned_df)
                quality_reporter_cleaned.save_report(cleaned_report)
                
                # Add to consolidated report
                consolidated_report.add_company_metrics(
                    company,
                    original_metrics,
                    cleaned_metrics
                )
                
                stats.successful.append(company)
                pbar.set_postfix(status="Success")
            else:
                stats.failed.append((company, "Cleaning failed"))
                pbar.set_postfix(status="Failed")
                
        except Exception as e:
            stats.failed.append((company, str(e)))
            pbar.set_postfix(status="Error")
            continue
    
    # Close progress bar
    pbar.close()
    
    # Print detailed processing report
    stats.print_detailed_report()
    
    # Generate consolidated report if we have successful processes
    if stats.successful:
        print("\nGenerating consolidated report...")
        consolidated_text = consolidated_report.generate_consolidated_report()
        consolidated_file = consolidated_report.save_consolidated_report(consolidated_text)
        print(f"Consolidated report saved to: {consolidated_file}")
    else:
        print("\nNo companies were successfully processed. No consolidated report generated.")

if __name__ == "__main__":
    main()