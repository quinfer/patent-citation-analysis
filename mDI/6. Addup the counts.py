import pandas as pd

# File paths
input_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\matched_output.csv'
output_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\accumulated_output.csv'

# Load the matched dataset
matched_df = pd.read_csv(input_file)

# Ensure `citing_patent_id` and `year` are in the correct data types
matched_df['citing_patent_id'] = matched_df['citing_patent_id'].astype(str)
matched_df['year'] = pd.to_numeric(matched_df['year'], errors='coerce').fillna(0).astype(int)

# Sort the dataset by `citing_patent_id` and `year` to ensure proper accumulation
matched_df.sort_values(by=['citing_patent_id', 'year'], inplace=True)

# Calculate accumulated counts for `citation_count` and `total_forward_citation_count`
matched_df['accumulated_citation_count'] = matched_df.groupby('citing_patent_id')['citation_count'].cumsum()
matched_df['accumulated_forward_citation_count'] = matched_df.groupby('citing_patent_id')['total_forward_citation_count'].cumsum()

# Save the updated dataset to a new CSV file
matched_df.to_csv(output_file, index=False)

# Print confirmation and preview the updated dataset
print(f"Accumulated dataset saved to '{output_file}'")
print(matched_df.head(10))  # Display the first 10 rows of the dataset
