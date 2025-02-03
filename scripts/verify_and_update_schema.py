import json
from pathlib import Path

def get_company_list():
    """Get list of companies from Data directory"""
    base_path = Path('Data')
    companies = [d.name for d in base_path.iterdir() if d.is_dir() and d.name != 'backup_20250131' and d.name != 'summary']
    return sorted(companies)

def update_workflow_schema():
    """Update the workflow schema with actual company names and structure"""
    companies = get_company_list()
    
    schema = {
        "config": {
            "base_path": "Data",
            "companies": companies
        },
        "workflow_steps": [
            "clean_data",
            "process_backward_citations",
            "process_forward_citations",
            "merge_citations",
            "calculate_di",
            "calculate_mdi"
        ],
        "required_folders": [
            "Backward citation",
            "Forward citation",
            "Backward citation/cleaned"
        ],
        "expected_files": [
            "{company}_cleaned.csv",
            "{company}.csv",
            "{company}_merged_backward_citations.parquet",
            "{company}_backward_citations.csv",
            "{company}_forward_citations.csv",
            "di_summary.json",
            "flag_count.csv",
            "flag_summary_detailed.csv",
            "flag_summary.json",
            "merged_cleaned_data.csv",
            "pure_f_summary.json"
        ],
        "data_requirements": {
            "required_columns": [
                "citing_patent_id",
                "forward_citation_count",
                "forward_cited_numbers",
                "forward_cited_dates",
                "backward_cited_numbers",
                "backward_cited_dates",
                "grant_date",
                "ipc_code"
            ],
            "optional_columns": [
                "application_date",
                "assignee_name"
            ]
        }
    }
    
    schema_path = Path('workflow_schema.json')
    with open(schema_path, 'w') as f:
        json.dump(schema, f, indent=4)
    
    print(f"Created {schema_path} with {len(companies)} companies")
    return schema

if __name__ == "__main__":
    schema = update_workflow_schema()
    print("\nSchema updated successfully!") 