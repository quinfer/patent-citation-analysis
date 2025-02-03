# Patent Analysis Methodology

## Overview
This methodology implements an enhanced patent citation analysis framework based on recent academic literature. The analysis consists of three main components:
1. Citation Network Analysis
2. Pure F Score Calculation
3. Disruption Indices (DI and mDI) Calculation

## 1. Citation Network Analysis
The citation analysis examines both forward and backward citations with the following metrics:

### Basic Metrics
- Total citations
- Unique citing patents
- Unique cited patents
- Citation network density

### Temporal Patterns
- Mean citation lag
- Median citation lag
- Citation age distribution (0-2, 2-5, 5-10, 10+ years)

### Network Position Metrics
- Forward connections
- Backward connections
- Network density
- k5 diversity score

### K5 Diversity Score
Measures technological diversity through:
- Patent class distribution
- Citation network spread
- Temporal distribution
- Connection ratios

## 2. Pure F Score
The Pure F score combines multiple factors to measure citation quality:

### Components
1. Temporal Factor
   - Weights recent citations higher
   - Applies time decay function

2. Network Factor
   - Based on citation network position
   - Considers network density

3. Quality Factor
   - Citation diversity
   - Citation density

### Calculation
```
Pure F = Temporal Factor * Network Factor * Quality Factor
```

## 3. Disruption Indices (DI and mDI)

### Traditional Disruption Index (DI)
Calculated as an average of three components:
```
DI = (j5 + i5 + k5) / 3
```

### Modified Disruption Index (mDI)
The modified version emphasizes component interaction:
```
mDI = j5 * (1 + i5) * (1 + k5)
```

Key differences:
1. **Multiplicative Interaction**: mDI uses multiplication instead of addition to capture interaction effects between components
2. **Non-linear Scaling**: The (1 + x) terms ensure that high scores in i5 and k5 have a greater impact
3. **Impact Emphasis**: j5 (forward citation impact) serves as the base multiplier

### Component Interpretation
- **j5**: Forward citation impact (0-1)
- **i5**: Development speed (0-1)
- **k5**: Citation diversity (0-1)

### Score Ranges
- **DI**: 0 to 1 (linear scale)
- **mDI**: 0 to 4 (non-linear scale)

### Use Cases
- **DI**: Better for comparing overall innovation impact
- **mDI**: Better for identifying breakthrough innovations where all components are strong

## Implementation Details
The analysis is implemented in a series of Python scripts:
1. `6_count_flags.py`: Citation network analysis
2. `7_calculate_pure_f.py`: Pure F score calculation
3. `8_calculate_di.py`: Disruption Index calculation
4. `9_generate_summary.py`: Results aggregation and visualization 