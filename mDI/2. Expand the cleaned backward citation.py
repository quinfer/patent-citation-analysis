import pandas as pd

# Load the data
data_path = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\merged_cleaned_data.csv'
df = pd.read_csv(data_path)

# Ensure the date column is in datetime format
df['forward_cited_date'] = pd.to_datetime(df['forward_cited_date'], errors='coerce')

# Extract the year from the forward_cited_date
df['forward_cited_year'] = df['forward_cited_date'].dt.year

# Group by citing_patent_id, citing_number, backward_cited_number, and forward_cited_year
# Then count the occurrences of forward_cited_number
result = (
    df.groupby(['citing_patent_id', 'citing_number', 'backward_cited_number', 'forward_cited_year'])
    .agg(forward_citation_count=('forward_cited_number', 'count'))
    .reset_index()
)

# Save the result to a CSV file
output_path = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\mDI_citation_counts_by_year.csv'
result.to_csv(output_path, index=False)

print(f"Forward citation counts by year saved to '{output_path}'")