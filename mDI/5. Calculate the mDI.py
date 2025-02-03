import pandas as pd

# File paths
input_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\matched_output.csv'
output_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\mDI_output.csv'

# Load the dataset
df = pd.read_csv(input_file)

# Ensure the relevant columns are numeric
df['citation_count'] = pd.to_numeric(df['citation_count'], errors='coerce')
df['total_forward_citation_count'] = pd.to_numeric(df['total_forward_citation_count'], errors='coerce')
df['DI_1'] = pd.to_numeric(df['DI_1'], errors='coerce')

# Calculate mDI using the provided formula
df['mDI'] = (
    df['citation_count'] / (df['citation_count'] + df['total_forward_citation_count'])
) * df['DI_1']

# Handle potential division by zero or missing values
df['mDI'] = df['mDI'].fillna(0)

# Save the updated dataset with mDI to a new CSV file
df.to_csv(output_file, index=False)

# Print confirmation and preview the updated dataset
print(f"mDI values calculated and saved to '{output_file}'")
print(df.head(10))  # Display the first 10 rows of the dataset
