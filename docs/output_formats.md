# Output File Formats

## Overview
This document describes the output formats for each stage of the patent analysis pipeline. Each step generates specific files with standardized structures.

## 1. Pure F Score Outputs
### Location: `Data/{company_name}/pure_f_summary.json`
```json
{
  "2023": {
    "company_name": "company_name",
    "year": 2023,
    "total_citations": 100,
    "matched_citations": 80,
    "pure_f_score": 0.8,
    "quality_metrics": {
      "match_rate": 0.75,
      "perfect_matches": 60,
      "no_matches": 10
    },
    "total_patents": 50,
    "processing_date": "2025-01-31"
  }
}
```

## 2. Disruption Index Outputs
### Location: `Data/{company_name}/di_summary.json`
```json
{
  "company_name": "company_name",
  "yearly_di": {
    "2023": {
      "disruption_index": 0.65,
      "components": {
        "pure_f_score": 0.8,
        "quality_factor": 0.85,
        "impact_factor": 0.95
      },
      "metrics": {
        "total_patents": 50,
        "total_citations": 100,
        "citations_per_patent": 2.0,
        "matched_citations_per_patent": 1.6
      },
      "quality_distribution": {
        "high_quality_matches": 60,
        "medium_quality_matches": 30,
        "low_quality_matches": 10,
        "poor_quality_matches": 0
      }
    }
  },
  "processing_date": "2025-01-31"
}
```

## 3. Panel Dataset
### Location: `Data/disruption_index_panel.csv`
```csv
company_name,year,disruption_index,pure_f_score,quality_factor,impact_factor,total_patents,total_citations,citations_per_patent,matched_citations_per_patent
company1,2020,0.65,0.80,0.85,0.95,100,1000,10.0,8.0
company1,2021,0.70,0.82,0.87,0.96,120,1200,10.0,8.2
company2,2020,0.55,0.75,0.80,0.92,80,800,10.0,7.5
```

## 4. Summary Reports
### Location: `Data/summary/`

### 4.1 Rankings Files
#### `rankings_by_di.csv`
```csv
company_name,disruption_index
company1,0.75
company2,0.70
```

#### `rankings_by_pure_f.csv`
```csv
company_name,pure_f_score
company1,0.85
company2,0.80
```

#### `rankings_by_citations.csv`
```csv
company_name,citations_per_patent
company1,12.5
company2,10.2
```

### 4.2 Summary Statistics
#### `summary_statistics.json`
```json
{
  "total_companies": 100,
  "total_patents": 50000,
  "total_citations": 500000,
  "average_di": 0.65,
  "median_di": 0.63,
  "average_pure_f": 0.75,
  "median_pure_f": 0.72,
  "generation_date": "2025-01-31"
}
```

## 5. Visualizations
### Location: `Data/summary/`

### 5.1 Distribution Plots
- `di_distribution.png`: Histogram of Disruption Index scores
- `pure_f_vs_di.png`: Scatter plot of Pure F scores vs Disruption Index
- `top_companies_di.png`: Bar chart of top 20 companies by DI

## Data Field Definitions

### Pure F Score Metrics
- `total_citations`: Total forward citations received
- `matched_citations`: Successfully matched citations
- `pure_f_score`: Ratio of matched to total citations (0-1)
- `match_rate`: Quality of citation matches (0-1)
- `perfect_matches`: Citations with exact matches
- `no_matches`: Citations without matches

### Disruption Index Components
- `disruption_index`: Final DI score (0-1)
- `quality_factor`: Weighted score of match quality (0-1)
- `impact_factor`: Citation impact score (0-1)
- `citations_per_patent`: Average citations per patent

### Quality Distribution Categories
- `high_quality_matches`: Perfect citation matches
- `medium_quality_matches`: Partial matches
- `low_quality_matches`: Poor matches
- `poor_quality_matches`: Failed matches

## File Naming Conventions
- All JSON files use snake_case naming
- CSV files use lowercase with underscores
- Dates format: YYYY-MM-DD
- Company names are standardized lowercase with underscores

## Best Practices
1. Always verify file integrity after generation
2. Check for expected fields in output files
3. Monitor file sizes for anomalies
4. Validate date ranges in panel data
5. Ensure consistent company naming across files