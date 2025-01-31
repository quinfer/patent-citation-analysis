# Methodology: Citation Matching and Disruption Index Analysis

This document outlines the methodology used to analyze patent citation data and calculate company-level disruption indices. The process involves two main stages: Pure F-score calculation for citation matching quality and Disruption Index computation for technological impact assessment.

## 1. Pure F-Score Calculation

The Pure F-score measures the quality of citation matching between patents. It is calculated using the following process:

### 1.1 Data Processing
- Loads citation matching summaries from `flag_summary.json` for each company
- Processes data year by year to calculate matching quality metrics
- Validates data completeness and structure before calculations

### 1.2 Pure F-Score Formula
```
Pure F-Score = matched_citations / total_forward_citations
```

Where:
- `matched_citations`: Number of successfully matched patent citations
- `total_forward_citations`: Total number of forward citations for all patents

### 1.3 Quality Metrics
For each year, the following quality metrics are tracked:
- Match rate: Average success rate of citation matching
- Perfect matches: Number of patents with all citations matched
- No matches: Number of patents with no successful matches
- Total patents: Number of patents analyzed

## 2. Disruption Index (DI) Calculation

The Disruption Index combines citation matching quality with impact metrics to measure a company's technological influence.

### 2.1 Formula
```
Disruption Index = Pure F-Score × Quality Factor × Impact Factor
```

### 2.2 Components

#### Quality Factor
Weighted score based on match quality distribution:
- High quality matches: Weight = 1.0
- Medium quality matches: Weight = 0.7
- Low quality matches: Weight = 0.4
- Poor quality matches: Weight = 0.1

Formula:
```
Quality Factor = Σ(weight × number_of_matches) / total_matches
```

#### Impact Factor
Logarithmic scale of citations per patent:
```
Impact Factor = min(1.0, 0.1 * (1 + ln(citations_per_patent)))
```

This scaling:
- Dampens the effect of extremely high citation counts
- Provides meaningful differentiation for typical citation ranges
- Returns 0 for patents with no citations

## 3. Output Data

### 3.1 Company-Level Results
For each company, the following files are generated:
- `pure_f_summary.json`: Pure F-scores and citation matching metrics by year
- `di_summary.json`: Disruption Index components and aggregate scores

### 3.2 Panel Dataset
A comprehensive CSV file (`disruption_index_panel.csv`) containing:
- Company and year identifiers
- Disruption Index scores and components
- Citation metrics and quality distributions
- Patent counts and matching statistics

## 4. Data Validation and Quality Control

### 4.1 Input Validation
- Checks for required data fields and proper data types
- Validates citation counts and patent numbers
- Ensures consistent data structure across years

### 4.2 Error Handling
- Logs processing errors and validation failures
- Tracks failed companies and processing issues
- Provides detailed error messages for debugging

### 4.3 Quality Metrics
- Monitors citation matching quality
- Tracks distribution of match quality levels
- Reports processing statistics and success rates

## 5. Implementation Details

### 5.1 File Structure
```
Data/
├── company_name/
│   ├── flag_summary.json
│   ├── pure_f_summary.json
│   └── di_summary.json
└── disruption_index_panel.csv

logs/
├── pure_f_calculation.log
└── disruption_index.log
```

### 5.2 Processing Steps
1. Load configuration from `workflow_schema_cleaned.json`
2. Calculate Pure F-scores for each company
3. Compute Disruption Index components
4. Generate company-level summaries
5. Create consolidated panel dataset
6. Produce processing logs and statistics

### 5.3 Dependencies
- Python 3.x
- pandas: Data manipulation and analysis
- numpy: Mathematical operations
- logging: Process tracking and error handling
- pathlib: File path management
- tqdm: Progress monitoring
