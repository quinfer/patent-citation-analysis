import pandas as pd

# Load the dataset
data_path = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\mDI_citation_counts_by_year.csv'
df = pd.read_csv(data_path)

# Group by citing_patent_id, citing_number, and forward_cited_year, summing up forward_citation_count
total_citation_count_by_year = (
    df.groupby(['citing_patent_id', 'citing_number', 'forward_cited_year'], as_index=False)
    .agg(total_forward_citation_count=('forward_citation_count', 'sum'))
)

# Save the result to a CSV file
output_path = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\mDI_total_forward_citation_by_year.csv'
total_citation_count_by_year.to_csv(output_path, index=False)

print(f"Total forward citation count by year saved to '{output_path}'")
