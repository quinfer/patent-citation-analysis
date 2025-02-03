import pandas as pd

# File paths
input_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\accumulated_output.csv'
output_file = r'C:\Users\40327155\PycharmProjects\pythonProject\data\1 Oracle International Corporation\final_accumulated_output.csv'

# Load the dataset
df = pd.read_csv(input_file)

# Ensure the relevant columns are numeric to avoid calculation errors
df['accumulated_citation_count'] = pd.to_numeric(df['accumulated_citation_count'], errors='coerce')
df['accumulated_forward_citation_count'] = pd.to_numeric(df['accumulated_forward_citation_count'], errors='coerce')
df['DI_1'] = pd.to_numeric(df['DI_1'], errors='coerce')

# Calculate the new value for each row
df['Accumulated_mDI'] = (
    df['accumulated_citation_count'] /
    (df['accumulated_citation_count'] + df['accumulated_forward_citation_count'])
) * df['DI_1']

# Handle potential division by zero or missing values
df['Accumulated_mDI'] = df['Accumulated_mDI'].fillna(0)

# Save the updated dataset to a new CSV file
df.to_csv(output_file, index=False)

# Print confirmation and preview the updated dataset
print(f"Final dataset with calculated values saved to '{output_file}'")
print(df.head(10))  # Display the first 10 rows of the dataset
