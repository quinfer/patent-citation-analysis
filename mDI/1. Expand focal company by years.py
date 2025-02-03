import pandas as pd
from pathlib import Path
from collections import Counter
import datetime


# Function to try different date formats
def parse_date(date_str):
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None  # Return None if no format matches


# Load your dataset
file_path = Path(r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\Oracle.csv')
df = pd.read_csv(file_path)

# Create a new DataFrame to hold the expanded data
expanded_data = []

# Iterate through each row of the original DataFrame
for index, row in df.iterrows():
    citing_patent_id = row['citing_patent_id']
    forward_cited_dates = row['forward_cited_dates']

    # Check if forward_cited_dates is not NaN
    if pd.notna(forward_cited_dates):
        # Split the forward_cited_dates into a list
        forward_cited_dates_list = forward_cited_dates.split(', ')

        # Extract the year from each citation date, using multiple formats
        citation_years = [parse_date(date).year for date in forward_cited_dates_list if parse_date(date)]

        # Count the occurrences of citations per year
        year_counts = Counter(citation_years)

        # Create a row with the citing_patent_id and year counts
        for year, count in year_counts.items():
            expanded_data.append({'citing_patent_id': citing_patent_id, 'year': year, 'citation_count': count})
    else:
        # If no forward_cited_dates, add a row with 0 citations (or skip, based on preference)
        expanded_data.append({'citing_patent_id': citing_patent_id, 'year': None, 'citation_count': 0})

# Convert the expanded data into a new DataFrame
expanded_df = pd.DataFrame(expanded_data)

# Save the expanded data to a new CSV file
output_file_path = Path(r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\mDI_count_by_year.csv')
expanded_df.to_csv(output_file_path, index=False)

# Display the first few rows of the expanded DataFrame
print(expanded_df.head())
