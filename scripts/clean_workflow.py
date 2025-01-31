import json
import re
import os
from pathlib import Path
import shutil

def clean_name(name):
    """Standardize name format"""
    return name.lower().replace(' ', '_').replace('&', 'and')

def clean_schema_and_folders(schema_path, base_data_path):
    """Clean both schema and actual folders"""
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    base_path = Path(base_data_path)
    changes_made = []
    errors = []

    # 1. Clean schema first
    schema['required_folders'] = [
        "cleaned",
        "Backward citation"
    ]
    
    # 2. Clean company names in schema
    schema['config']['companies'] = [
        clean_name(company) for company in schema['config']['companies']
    ]

    # 3. Process each company folder
    for company_folder in base_path.glob('*'):
        if not company_folder.is_dir():
            continue
            
        old_name = company_folder.name
        new_name = clean_name(old_name)
        
        try:
            # Rename company folder if needed
            if old_name != new_name:
                new_path = company_folder.parent / new_name
                company_folder.rename(new_path)
                changes_made.append(f"Renamed folder: {old_name} -> {new_name}")
                company_folder = new_path

            # Fix Backward citation folder naming
            bc_variations = ['Backward citation', 'Backward citaion', 'backward_citation']
            for bc_var in bc_variations:
                old_bc_path = company_folder / bc_var
                if old_bc_path.exists():
                    new_bc_path = company_folder / 'Backward citation'
                    if old_bc_path != new_bc_path:
                        old_bc_path.rename(new_bc_path)
                        changes_made.append(f"Renamed in {new_name}: {bc_var} -> Backward citation")

            # Ensure 'cleaned' folder exists in Backward citation
            bc_path = company_folder / 'Backward citation'
            if bc_path.exists():
                cleaned_path = bc_path / 'cleaned'
                cleaned_path.mkdir(exist_ok=True)

            # Rename CSV files to standard format
            for csv_file in company_folder.rglob('*.csv'):
                old_file_name = csv_file.name
                # Standardize number range format in filenames
                new_file_name = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1_\2', old_file_name)
                new_file_name = clean_name(new_file_name)
                
                if old_file_name != new_file_name:
                    new_file_path = csv_file.parent / new_file_name
                    csv_file.rename(new_file_path)
                    changes_made.append(f"Renamed file in {new_name}: {old_file_name} -> {new_file_name}")

        except Exception as e:
            errors.append(f"Error processing {old_name}: {str(e)}")

    # 4. Update expected_files in schema based on actual files
    all_files = set()
    for company_folder in base_path.glob('*'):
        if company_folder.is_dir():
            for csv_file in company_folder.rglob('*.csv'):
                all_files.add(clean_name(csv_file.name))
    
    schema['expected_files'] = sorted(list(all_files))

    return schema, changes_made, errors

def save_schema(schema, output_path):
    """Save the cleaned schema to file"""
    with open(output_path, 'w') as f:
        json.dump(schema, f, indent=4)

def main():
    # Paths
    schema_path = 'workflow_schema.json'
    base_data_path = Path.cwd() / 'Data'  # Adjust as needed
    
    # Clean schema and folders
    cleaned_schema, changes, errors = clean_schema_and_folders(schema_path, base_data_path)
    
    # Save cleaned schema
    save_schema(cleaned_schema, 'workflow_schema_cleaned.json')
    
    # Print report
    print("\n=== Cleaning Report ===")
    
    print("\nChanges Made:")
    for change in changes:
        print(f"- {change}")
    
    if errors:
        print("\nErrors Encountered:")
        for error in errors:
            print(f"- {error}")
    
    print(f"\nTotal changes: {len(changes)}")
    print(f"Total errors: {len(errors)}")
    print("\nCleaned schema saved to 'workflow_schema_cleaned.json'")

if __name__ == "__main__":
    main()