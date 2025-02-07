# Output File Formats

## 1. Panel Dataset Structure
### Location: `Data/summary/disruption_panel.{csv,parquet}`

#### Core Fields
| Field | Type | Description | Range |
|-------|------|-------------|--------|
| company_name | string | Company identifier | - |
| year | int | Year of observation | 1836-2023 |

#### Disruption Measures
| Field | Type | Description | Range |
|-------|------|-------------|--------|
| disruption_index | float | Traditional DI (j5+i5+k5)/3 | [0,1] |
| modified_disruption_index | float | mDI = j5*(1+i5)*(1+k5) | [0,4] |

#### Component Scores
| Field | Type | Description | Range |
|-------|------|-------------|--------|
| j5_score | float | Forward citation impact | [0,1] |
| i5_score | float | Development speed | [0,1] |
| k5_score | float | Citation diversity | [0,1] |

#### Network Metrics
| Field | Type | Description | Range |
|-------|------|-------------|--------|
| pure_f_score | float | Citation matching quality | [0,∞) |
| total_citations | int | Number of forward citations | ≥0 |
| network_density | float | Citation network density | [0,∞) |

### Example Data
```csv
company_name,year,disruption_index,modified_disruption_index,j5_score,i5_score,k5_score,pure_f_score,total_citations,network_density
abbott,1841,0.667,2.000,1.000,0.000,1.000,9.500,37,18.500
abbott,1861,0.600,1.800,1.000,0.000,0.800,1.000,1,1.000
```

### Economic Interpretation

#### Disruption Measures
- **disruption_index**: Linear measure of technological disruption
- **modified_disruption_index**: Non-linear measure capturing interaction effects

#### Component Scores
- **j5_score**: Market impact and technological influence
- **i5_score**: Speed of knowledge development
- **k5_score**: Breadth of technological influence

#### Network Metrics
- **pure_f_score**: Quality of knowledge transmission
- **network_density**: Intensity of knowledge flows
- **total_citations**: Scale of technological impact

## 2. File Formats

### Parquet Format
- Primary format for analysis
- Efficient storage and retrieval
- Maintains data types
- Supports partitioning

### CSV Format
- Secondary format for accessibility
- Human-readable
- Compatible with most tools
- Useful for quick inspection

## 3. Best Practices

### Data Validation
1. Check value ranges:
```python
assert df['disruption_index'].between(0, 1).all()
assert df['modified_disruption_index'].between(0, 4).all()
assert df['j5_score'].between(0, 1).all()
```

### Missing Values
- No missing values in key metrics
- Zero values are meaningful
- Validate temporal coverage

### Temporal Considerations
- Recent years may be incomplete
- Citation lag effects
- Field-specific patterns

## 4. Usage Notes

### Loading Data
```python
# Preferred method (Parquet)
import pandas as pd
df = pd.read_parquet('Data/summary/disruption_panel.parquet')

# Alternative (CSV)
df = pd.read_csv('Data/summary/disruption_panel.csv')
```

### Basic Analysis
```python
# Summary statistics
summary = df.groupby('company_name').agg({
    'disruption_index': ['mean', 'std'],
    'modified_disruption_index': ['mean', 'std'],
    'total_citations': 'sum'
})
```

### Time Series Analysis
```python
# Yearly trends
yearly = df.groupby('year').agg({
    'disruption_index': 'mean',
    'modified_disruption_index': 'mean'
}).reset_index()
```

## 5. Field-Specific Considerations

### Technology Fields
- Chemical
- Computers & Communications
- Drugs & Medical
- Electrical & Electronic
- Mechanical
- Others

### Field-Specific Metrics
- Baseline disruption levels
- Citation patterns
- Network density norms