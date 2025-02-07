# Patent Innovation Analysis Pipeline

## Overview
This project implements a network-based patent citation analysis framework following Funk & Owen-Smith (2017) to measure technological disruption and innovation patterns.

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run complete pipeline
python scripts/6_count_flags.py
python scripts/7_calculate_pure_f.py
python scripts/8_calculate_di.py
python scripts/9_generate_summary.py

# Generate report
quarto render summary_report.qmd
```
## Project Structure
```
.
├── Data/
│   ├── company_name/           # Company-specific data
│   │   ├── citation_analysis.json
│   │   ├── pure_f_summary.json
│   │   ├── disruption_index.json
│   │   └── merged_citations.parquet
│   └── summary/               # Aggregate results
│       ├── disruption_panel.parquet  # Main panel dataset
│       ├── yearly_averages.csv
│       └── figures/
├── docs/
│   ├── METHODOLOGY.md         # Technical details
│   ├── DATA_DICTIONARY.md     # Panel data documentation
│   ├── OUTPUT_FORMATS.md      # File specifications
│   ├── VISUALIZATION.md       # Plotting guidelines
│   └── TODO.md               # Development roadmap
├── scripts/                  # Analysis pipeline
├── logs/                    # Processing logs
└── README.md
```

## Key Features

### ✅ Implemented
1. **Citation Network Analysis**
   - Basic citation metrics
   - Temporal patterns
   - Network density
   - K5 diversity score

2. **Pure F Score**
   - Citation matching quality
   - Temporal weighting
   - Network position adjustment

3. **Disruption Indices**
   - Traditional DI (j5, i5, k5)
   - Modified DI (mDI)
   - Panel data generation

4. **Visualizations**
   - Distribution analysis
   - Time series trends
   - Component correlations

### 🚧 Upcoming
1. **USPTO Classification**
   - Technology field mapping
   - NBER categories
   - Field-specific metrics

2. **Network Consolidation**
   - Field-specific measures
   - Cross-field citations
   - Temporal stability

## Data Structure and Outputs

### Panel Dataset
Our primary output is a comprehensive panel dataset containing:
- Disruption Indices (DI and mDI)
- Component scores (j5, i5, k5)
- Network metrics
- Citation counts

Example:
```csv
company_name,year,disruption_index,modified_disruption_index,j5_score,i5_score,k5_score,pure_f_score,total_citations,network_density
abbott,1841,0.667,2.000,1.000,0.000,1.000,9.500,37,18.500
```

### Output Files
- `disruption_panel.parquet`: Primary analysis dataset
- `yearly_averages.csv`: Temporal trends
- `summary_statistics.csv`: Cross-sectional statistics
- Visualizations in `Data/summary/figures/`

See [Output Formats Documentation](docs/output_formats.md) for detailed specifications of all data structures and file formats.

## Documentation

- [Methodology](docs/METHODOLOGY.md) - Detailed technical implementation
- [Data Dictionary](docs/DATA_DICTIONARY.md) - Panel dataset documentation
- [Visualization](docs/VISUALIZATION.md) - Plotting guidelines

## Development Status
See our detailed implementation roadmap and upcoming features in [TODO.md](docs/TODO.md)

## Dependencies
```python
pandas>=1.3.0
numpy>=1.20.0
networkx>=2.6.0
matplotlib>=3.4.0
seaborn>=0.11.0
tqdm>=4.61.0
quarto>=0.1.0
```

## Example Output

### Disruption Index Distribution
![DI Distribution](Data/summary/figures/di_distribution.png)

### Time Series Trends
![Time Series](Data/summary/figures/di_time_series.png)

## Usage

### Basic Analysis
```python
from scripts.calculate_di import DisruptionIndexCalculator

# Initialize calculator
calculator = DisruptionIndexCalculator()

# Process company
results = calculator.calculate_company_di("company_name")
```

### Generating Summaries
```python
from scripts.generate_summary import SummaryGenerator

# Initialize generator
generator = SummaryGenerator()

# Create panel dataset
panel_df = generator.generate_summary()
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Submit pull request

## Citation
If you use this code in your research, please cite:

```bibtex
@article{funk2017dynamic,
  title={A Dynamic Network Measure of Technological Change},
  author={Funk, Russell J and Owen-Smith, Jason},
  journal={Management Science},
  volume={63},
  number={3},
  pages={791--817},
  year={2017}
}
```

## License
MIT License