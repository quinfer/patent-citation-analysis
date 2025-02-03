import pandas as pd
import os

# File paths
di_summary_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\DI_summary.csv'
total_forward_citation_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\mDI_total_forward_citation_by_year.csv'
citation_count_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\mDI_count_by_year.csv'
output_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\matched_output.csv'

# Verify files exist
files = [di_summary_file, total_forward_citation_file, citation_count_file]
for file in files:
    if not os.path.exists(file):
        raise FileNotFoundError(f"File not found: {file}")

# Load datasets
di_summary_df = pd.read_csv(di_summary_file)
total_forward_citation_df = pd.read_csv(total_forward_citation_file)
citation_count_df = pd.read_csv(citation_count_file)

# Ensure citing_patent_id is consistent
di_summary_df['citing_patent_id'] = di_summary_df['citing_patent_id'].astype(str)
total_forward_citation_df['citing_patent_id'] = total_forward_citation_df['citing_patent_id'].astype(str)
citation_count_df['citing_patent_id'] = citation_count_df['citing_patent_id'].astype(str)

# Create a complete set of `citing_patent_id` and `year` combinations
all_years = range(
    total_forward_citation_df['forward_cited_year'].min(),
    total_forward_citation_df['forward_cited_year'].max() + 1
)
all_citing_patent_ids = pd.concat([
    di_summary_df['citing_patent_id'],
    total_forward_citation_df['citing_patent_id'],
    citation_count_df['citing_patent_id']
]).drop_duplicates()

# Create a complete index of `citing_patent_id` and `year`
complete_index = pd.MultiIndex.from_product(
    [all_citing_patent_ids, all_years],
    names=['citing_patent_id', 'year']
)
complete_df = pd.DataFrame(index=complete_index).reset_index()

# Merge DI summary with the complete index
merged_df = pd.merge(complete_df, di_summary_df[['citing_patent_id', 'DI_1']], on='citing_patent_id', how='left')

# Merge with citation count data
merged_df = pd.merge(merged_df, citation_count_df[['citing_patent_id', 'year', 'citation_count']], on=['citing_patent_id', 'year'], how='left')

# Merge with total forward citation data
merged_df = pd.merge(merged_df, total_forward_citation_df[['citing_patent_id', 'forward_cited_year', 'total_forward_citation_count']],
                     left_on=['citing_patent_id', 'year'], right_on=['citing_patent_id', 'forward_cited_year'], how='left')

# Fill missing values
merged_df['DI_1'] = merged_df['DI_1'].fillna(0)
merged_df['citation_count'] = merged_df['citation_count'].fillna(0)
merged_df['total_forward_citation_count'] = merged_df['total_forward_citation_count'].fillna(0)

# Drop unnecessary column after merge
merged_df.drop(columns=['forward_cited_year'], inplace=True, errors='ignore')

# Sort the dataset
merged_df.sort_values(by=['citing_patent_id', 'year'], inplace=True)

# Save the final dataset to a CSV file
merged_df.to_csv(output_file, index=False)

# Print confirmation and preview the merged dataset
print(f"Matched dataset saved to '{output_file}'")
print(merged_df.head(10))
