import json
from pathlib import Path

def update_workflow_schema():
    """Update the workflow schema with all required keys"""
    
    schema = {
        "config": {
            "base_path": "Data",
            "companies": ["example_company"]
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
            "cleaned",
            "Backward citation",
            "Forward citation",
            "reports"
        ],
        "expected_files": [
            "flag_summary.json",
            "pure_f_summary.json",
            "di_summary.json",
            "mdi_summary.json"
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
    
    # Save schema
    schema_path = Path('workflow_schema.json')
    with open(schema_path, 'w') as f:
        json.dump(schema, f, indent=4)
    
    print(f"Created {schema_path} with all required keys")
    return schema

if __name__ == "__main__":
    updated_schema = update_workflow_schema()
    print("\nUpdated Schema Contents:")
    print(json.dumps(updated_schema, indent=2)) 