# Patent Innovation Analysis Pipeline

## Overview
This project analyzes patent innovation patterns using disruption indices based on citation networks. The methodology follows Park et al. (2023)'s disruption index framework.

## Project Structure
```
.
├── Data/
│   ├── raw/                  # Raw patent data
│   ├── processed/            # Processed patent files
│   └── summary/             # Analysis outputs and visualizations
├── scripts/
│   ├── 1_process_patents.py  # Initial data processing
│   ├── 2_clean_data.py      # Data cleaning and standardization
│   ├── 3_extract_citations.py # Citation network extraction
│   ├── 4_build_networks.py   # Network construction
│   ├── 5_calculate_metrics.py # Basic metric calculations
│   ├── 6_temporal_analysis.py # Temporal metric calculations
│   ├── 7_network_analysis.py  # Network metric calculations
│   ├── 8_calculate_di.py     # Disruption Index calculation
│   └── 9_generate_summary.py # Summary statistics and visualizations
├── logs/                    # Processing logs
├── summary_report.qmd       # Quarto report template
├── requirements.txt
└── README.md
```

## Key Features
- Comprehensive patent data processing pipeline
- Citation network analysis
- Disruption Index (DI) and Modified Disruption Index (MDI) calculations
- Component analysis (j5, i5, k5 scores)
- Temporal trend analysis
- Network density metrics
- Statistical summaries and visualizations

## Output Files
- `disruption_panel.parquet`: Complete panel dataset
- `disruption_summary_stats.csv`: Statistical summaries
- `yearly_averages.csv`: Yearly metric averages
- Visualizations:
  - Component correlations
  - DI/MDI distributions
  - Time series trends

## Methodological Notes
- Analysis covers patent data from 1836 to 2023
- Recent years (2023-2024) may show incomplete data due to patent processing lag
- Network metrics require time to stabilize
- Citation accumulation patterns affect recent patent metrics

## Dependencies
```
pandas
numpy
networkx
matplotlib
seaborn
tqdm
quarto
```

## Usage
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the complete pipeline:
```bash
python scripts/1_process_patents.py
python scripts/2_clean_data.py
python scripts/3_extract_citations.py
python scripts/4_build_networks.py
python scripts/5_calculate_metrics.py
python scripts/6_temporal_analysis.py
python scripts/7_network_analysis.py
python scripts/8_calculate_di.py
python scripts/9_generate_summary.py
```

3. Generate the report:
```bash
quarto render summary_report.qmd
```

## References
1. Funk, Russell J., and Owen-Smith, Jason. "A Dynamic Network Measure of Technological Change." *Management Science* 63.3 (2017): 791-817. [https://doi.org/10.1287/mnsc.2015.2366](https://doi.org/10.1287/mnsc.2015.2366)
2. Wu, Lingfei, Dashun Wang, and James A. Evans. "Large Teams Develop and Small Teams Disrupt Science and Technology." *Nature* 566.7744 (2019): 378-382. [https://doi.org/10.1038/s41586-019-0941-9](https://doi.org/10.1038/s41586-019-0941-9)
3. Uzzi, Brian, et al. "Atypical Combinations and Scientific Impact." *Science* 342.6157 (2013): 468-472. [https://doi.org/10.1126/science.1240474](https://doi.org/10.1126/science.1240474)

## Contributing
Please submit issues and pull requests for any improvements or bug fixes.

## License
MIT

# TO-DO: Technology Field Classification and Weighting

## Planned Extensions
Following Funk & Owen-Smith (2017), we need to implement technology field-specific analysis based on USPTO classification and consolidation patterns.

### 1. Technology Classification Processing
- Extract USPTO technology classes
- Implement NBER technology field categorization
- Handle temporal changes in classification systems
```python
# Example planned implementation
def process_tech_classes(patent_data):
    """
    Process USPTO technology classes following Funk & Owen-Smith (2017).
    - Extract primary and cross-reference classifications
    - Map to NBER categories
    - Handle temporal classification changes
    """
    pass
```

### 2. Field-Specific Analysis Schema
Based on Funk & Owen-Smith (2017):
- Six main technological categories:
  1. Chemical
  2. Computers & Communications
  3. Drugs & Medical
  4. Electrical & Electronic
  5. Mechanical
  6. Others

```python
TECH_CATEGORIES = {
    'Chemical': ['520', '530', ...],  # USPTO classes
    'Computers': ['700', '710', ...],
    'Drugs': ['424', '514', ...],
    'Electrical': ['360', '370', ...],
    'Mechanical': ['123', '180', ...],
    'Others': ['002', '004', ...]
}
```

### 3. Implementation Steps
1. **Classification Processing**
   - Extract USPTO classes
   - Map to NBER categories
   - Handle temporal changes

2. **Network Measures**
   - Calculate consolidated network measures
   - Implement field-specific thresholds
   - Account for temporal variations

3. **Pure-F Score Calculation**
   - Field-specific Pure-F scores
   - Temporal normalization
   - Cross-field comparisons

### 4. Required Data
- Complete USPTO classification history
- NBER technology category mappings
- Historical classification changes

### 5. Impact on Current Metrics
Will affect:
- Pure-F score calculations
- Network consolidation measures
- Temporal comparisons
- Cross-field normalization

### 6. Technical Requirements
Additional dependencies:
```
# To be added to requirements.txt
uspto-parser
nber-classifier
networkx>=2.0
```

### 7. Expected Outputs
New files:
- `tech_classification.json`: Technology field mappings
- `field_network_metrics.csv`: Field-specific network measures
- `consolidated_measures.parquet`: Consolidated analysis results

### 8. Validation Approaches
Following Funk & Owen-Smith (2017):
- Consolidation patterns by field
- Temporal stability tests
- Cross-field citation patterns
- Robustness checks

## Priority Tasks
1. [ ] Implement USPTO class extraction
2. [ ] Create NBER category mapping
3. [ ] Calculate field-specific network measures
4. [ ] Modify Pure-F calculation
5. [ ] Update visualization pipeline
6. [ ] Validate against Funk & Owen-Smith results

## References
Funk, Russell J., and Owen-Smith, Jason. "A Dynamic Network Measure of Technological Change." Management Science 63.3 (2017): 791-817.

Key sections:
- Section 3: Network Consolidation
- Section 4: Pure Consolidation Measure
- Appendix: Classification Details