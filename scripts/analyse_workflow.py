import os
from pathlib import Path
import pandas as pd
from collections import defaultdict
import json

def analyze_data_folder(base_path):
    """
    Analyze the Data folder structure and file patterns
    """
    base_path = Path(base_path)
    structure = defaultdict(dict)
    
    # Find all company folders
    company_folders = [f for f in base_path.iterdir() if f.is_dir()]
    
    for company_folder in company_folders:
        company_name = company_folder.name
        structure[company_name] = {
            'files': [],
            'folders': [],
            'file_patterns': set(),
            'csv_columns': defaultdict(set)
        }
        
        # Analyze folder structure
        for root, dirs, files in os.walk(company_folder):
            rel_path = Path(root).relative_to(company_folder)
            
            # Store folders
            if dirs:
                structure[company_name]['folders'].extend(dirs)
            
            # Analyze files
            for file in files:
                if file.endswith('.csv'):
                    full_path = Path(root) / file
                    rel_file_path = full_path.relative_to(company_folder)
                    structure[company_name]['files'].append(str(rel_file_path))
                    structure[company_name]['file_patterns'].add(file.split('_')[0] if '_' in file else file)
                    
                    # Sample CSV columns (reading just header)
                    try:
                        df = pd.read_csv(full_path, nrows=0)
                        structure[company_name]['csv_columns'][str(rel_file_path)] = list(df.columns)
                    except Exception as e:
                        print(f"Error reading {full_path}: {str(e)}")
    
    return structure

def print_analysis(structure):
    """
    Print a formatted analysis of the folder structure
    """
    print("\n=== Data Folder Analysis ===\n")
    
    # Find common patterns across all companies
    all_file_patterns = set()
    all_folders = set()
    
    for company_data in structure.values():
        all_file_patterns.update(company_data['file_patterns'])
        all_folders.update(company_data['folders'])
    
    print("Common File Patterns Found:")
    for pattern in sorted(all_file_patterns):
        print(f"- {pattern}")
    
    print("\nCommon Folders Found:")
    for folder in sorted(all_folders):
        print(f"- {folder}")
    
    print("\nDetailed Company Analysis:")
    for company, data in structure.items():
        print(f"\n{company}:")
        print("Files:")
        for file in sorted(data['files']):
            print(f"  - {file}")
            if file in data['csv_columns']:
                print(f"    Columns: {', '.join(data['csv_columns'][file])}")

def generate_updated_schema(structure):
    """
    Generate an updated workflow schema based on the analysis
    """
    schema = {
        'config': {
            'base_path': str(Path.cwd() / 'Data'),
            'companies': list(structure.keys())
        },
        'required_folders': list(set().union(*[set(d['folders']) for d in structure.values()])),
        'expected_files': list(set().union(*[set(d['file_patterns']) for d in structure.values()])),
        'workflow_steps': [
            "clean_focal_company",
            "clean_backward_citations",
            "merge_cleaned_citations",
            "rematch_forward_citations",
            "count_flags",
            "calculate_pure_f",
            "calculate_di"
        ]
    }
    
    return schema

def main():
    # Analyze current directory's Data folder
    base_path = Path.cwd() / 'Data'
    if not base_path.exists():
        print(f"Error: Data folder not found at {base_path}")
        return
    
    # Analyze structure
    structure = analyze_data_folder(base_path)
    
    # Print analysis
    print_analysis(structure)
    
    # Generate and save updated schema
    schema = generate_updated_schema(structure)
    
    # Save schema to JSON file
    schema_file = Path.cwd() / 'workflow_schema.json'
    with open(schema_file, 'w') as f:
        json.dump(schema, f, indent=4)
    
    print(f"\nWorkflow schema saved to {schema_file}")

if __name__ == "__main__":
    main()