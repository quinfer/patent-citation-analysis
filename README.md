# Patent Citation Analysis Pipeline

A comprehensive pipeline for analyzing patent citations and calculating disruption indices.

## Overview
This project processes patent citation data to:
- Match and validate citations
- Calculate Pure F scores
- Generate Disruption Indices (DI)
- Create visualization reports

## Pipeline Steps
1. Data Preparation (steps 1-5)
2. Citation Matching (step 6)
3. Pure F Score Calculation (step 7)
4. Disruption Index Analysis (step 8)
5. Summary Generation (step 9)

## Directory Structure
````

project/
├── Data/                    # Company data directory
│   └── company_name/        # Individual company folders
│       ├── flag_summary.json
│       ├── pure_f_summary.json
│       └── di_summary.json
├── docs/                    # Documentation
│   ├── methodology.md       # Analysis methodology
│   ├── configuration.md     # Setup instructions
│   └── output_formats.md    # File specifications
├── logs/                    # Log files
│   ├── pure_f_calculation.log
│   └── disruption_index.log
├── scripts/                 # Analysis scripts
│   ├── 6_count_flags.py
│   ├── 7_calculate_pure_f.py
│   ├── 8_calculate_di.py
│   └── 9_generate_summary.py
├── workflow_schema.json     # Configuration file
├── requirements.txt
└── README.md
````

## Setup
````bash
# Clone the repository
git clone [repository-url]

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p Data logs
````

## Running the Analysis

### Option 1: Run from Project Root
Run scripts directly from the project root:
````bash
python scripts/6_count_flags.py
python scripts/7_calculate_pure_f.py
python scripts/8_calculate_di.py
python scripts/9_generate_summary.py
````

### Option 2: Add Scripts to Python Path
Add scripts directory to Python path:
````bash
# On Unix/macOS
export PYTHONPATH=$PYTHONPATH:$(pwd)/scripts

# On Windows (PowerShell)
$env:PYTHONPATH += ";$pwd\scripts"

# Then run scripts
python 6_count_flags.py
python 7_calculate_pure_f.py
python 8_calculate_di.py
python 9_generate_summary.py
````

### Option 3: Use Run Script
Create and use a run script:
````bash
# create_run.sh (Unix/macOS)
#!/bin/bash
python scripts/6_count_flags.py
python scripts/7_calculate_pure_f.py
python scripts/8_calculate_di.py
python scripts/9_generate_summary.py

# Make executable
chmod +x create_run.sh
./create_run.sh
````

## Configuration
1. Update `workflow_schema.json` with:
   - Company list
   - Data paths
   - Required folders
   - Expected file patterns

2. Ensure data structure:
   - Company folders in `Data/`
   - Citation files in correct format
   - Required subfolders present

## Outputs
The pipeline generates:
1. Company-Level Files:
   - `pure_f_summary.json`: Citation matching metrics
   - `di_summary.json`: Disruption Index scores
   
2. Consolidated Data:
   - `disruption_index_panel.csv`: Complete panel dataset
   
3. Summary Reports:
   - Rankings by different metrics
   - Statistical summaries
   - Visualizations

4. Log Files:
   - Processing progress
   - Error tracking
   - Data validation results

## Documentation
Detailed documentation in `/docs`:
- `methodology.md`: Analysis process and formulas
- `configuration.md`: Setup and configuration guide
- `output_formats.md`: File structure specifications

## Requirements
- Python 3.x
- pandas
- numpy
- matplotlib
- seaborn
- tqdm

## Troubleshooting
1. Check log files in `logs/` directory
2. Verify Python path includes scripts directory
3. Ensure all dependencies are installed
4. Validate data structure against configuration
5. Check file permissions and paths

## Support
For issues and questions:
1. Check documentation in `/docs`
2. Review log files
3. Contact repository maintainers

## License
MIT License
