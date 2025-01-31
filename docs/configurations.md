# Configuration Guide

## Overview
This document describes the configuration system used in the patent analysis pipeline. The configuration is managed through a JSON schema file (`workflow_schema.json`) that defines the data structure, company list, and workflow steps.

## Schema Structure

### Base Configuration
```json
{
    "config": {
        "base_path": "/path/to/data/directory",
        "companies": [
            "company1",
            "company2",
            ...
        ]
    }
}
```

- `base_path`: Root directory containing all company data
- `companies`: List of companies to process (names are automatically standardized)

### Required Folder Structure
```json
{
    "required_folders": [
        "cleaned",
        "Backward citation"
    ]
}
```

Each company directory must contain:
- `cleaned/`: Directory for processed data files
- `Backward citation/`: Directory containing backward citation data

### File Naming Conventions
The pipeline expects specific file naming patterns:
1. Company-specific files:
   - `{company_name}.csv`: Raw company data
   - `{company_name}_cleaned.csv`: Processed company data

2. Citation range files:
   - Format: `{start_number}_{end_number}.csv`
   - Example: `10500000_11200000.csv`

## Data Directory Structure
```
Data/
├── company_name/
│   ├── company_name.csv
│   ├── company_name_cleaned.csv
│   └── Backward citation/
│       ├── cleaned/
│       └── citation_files.csv
```

## Workflow Steps
The pipeline follows these sequential steps:
```json
{
    "workflow_steps": [
        "clean_focal_company",
        "clean_backward_citations",
        "merge_cleaned_citations",
        "rematch_forward_citations",
        "count_flags",
        "calculate_pure_f",
        "calculate_di"
    ]
}
```

## File Standardisation
The configuration system automatically:
1. Standardises company names:
   - Converts to lowercase
   - Replaces spaces with underscores
   - Replaces '&' with 'and'

2. Standardizes file names:
   - Converts number ranges to underscore format
   - Maintains consistent case and spacing

## Schema Validation
The pipeline includes tools to:
1. Analyze existing data structure (`analyse_workflow.py`)
2. Clean and standardize configuration (`clean_workflow.py`)
3. Generate updated schema based on actual data

## Usage Example
1. Initialize configuration:
```python
# Load and validate schema
schema_path = Path('workflow_schema.json')
with open(schema_path) as f:
    schema = json.load(f)

# Access configuration
base_path = Path(schema['config']['base_path'])
companies = schema['config']['companies']
```

2. Clean existing configuration:
```bash
python clean_workflow.py
```

3. Analyze data structure:
```bash
python analyse_workflow.py
```

## Best Practices
1. Always use the cleaned schema version (`workflow_schema_cleaned.json`)
2. Run analysis before major processing to ensure data structure
3. Keep company names consistent across all files
4. Maintain the required folder structure for each company
5. Follow the standardized file naming conventions

## Troubleshooting
Common issues:
1. Inconsistent folder names: Run `clean_workflow.py`
2. Missing required folders: Check company directory structure
3. File naming issues: Verify against schema's expected_files
4. Path issues: Ensure base_path is correctly set
```