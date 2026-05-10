"""
Batch Load Real Data to BigQuery

Load summary.jsonl (with predefined schema) and ip_locations.jsonl to BigQuery
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from google.cloud import bigquery

# Import the load functions from gcs_to_bigquery module
import sys
sys.path.insert(0, str(Path(__file__).parent))
from gcs_to_bigquery import (
    get_bigquery_connection,
    close_bigquery_connection,
    load_jsonl_to_bigquery,
    load_csv_to_bigquery
)


def load_schema_from_file(schema_file: str) -> Optional[List[Dict]]:
    """
    Load BigQuery schema from JSON file.
    
    Args:
        schema_file: Path to JSON file containing schema
    
    Returns:
        List of schema field dicts or None if file not found
    """
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        print(f"✓ Loaded schema from {schema_file}")
        print(f"  Fields: {len(schema)}")
        return schema
    except FileNotFoundError:
        print(f"⚠️  Schema file not found: {schema_file}")
        return None
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in schema file: {schema_file}")
        return None
    except Exception as e:
        print(f"✗ Error loading schema: {e}")
        return None


def batch_load_real_data(
    dataset_id: str = "MongoDB_001",
    schema_file: str = "./output/bigquery_schema.json"
) -> Dict[str, Any]:
    """
    Batch load all real data files to BigQuery.
    
    Args:
        dataset_id: BigQuery dataset ID
        schema_file: Path to BigQuery schema file for summary.jsonl
    
    Returns:
        Dictionary with batch load results
    """
    results = {
        "status": "in_progress",
        "timestamp": datetime.now().isoformat(),
        "files": {},
        "summary": {
            "total_files": 3,
            "successful": 0,
            "failed": 0
        }
    }
    
    try:
        print("=" * 80)
        print("BATCH LOAD: Real Data Files to BigQuery")
        print("=" * 80)
        
        # Load schema for summary.jsonl
        print("\n[Preparation] Loading BigQuery schema...")
        print("-" * 80)
        schema = load_schema_from_file(schema_file)
        
        # File 1: summary.jsonl with autodetect (actual data structure may differ from schema)
        print("\n[File 1] Loading summary.jsonl (31.73 GB)...")
        print("-" * 80)
        success, message, job_result = load_jsonl_to_bigquery(
            gcs_uri="gs://mongodb-0001/real-data/extracted/summary.jsonl",
            dataset_id=dataset_id,
            table_id="summary_data",
            schema=None,  # Use autodetect for actual data structure
            autodetect_schema=True,
            write_disposition="WRITE_TRUNCATE"
        )
        
        results["files"]["summary.jsonl"] = {
            "status": "success" if success else "error",
            "message": message,
            "result": job_result
        }
        
        if success:
            results["summary"]["successful"] += 1
            print(f"\n✓ summary.jsonl loaded successfully")
        else:
            results["summary"]["failed"] += 1
            print(f"\n✗ summary.jsonl failed: {message}")
        
        # File 2: ip_locations.jsonl
        print("\n[File 2] Loading ip_locations.jsonl...")
        print("-" * 80)
        success, message, job_result = load_jsonl_to_bigquery(
            gcs_uri="gs://mongodb-0001/real-data/extracted/ip_locations_20260506_105815.jsonl",
            dataset_id=dataset_id,
            table_id="ip_locations",
            autodetect_schema=True,
            write_disposition="WRITE_TRUNCATE"
        )
        
        results["files"]["ip_locations.jsonl"] = {
            "status": "success" if success else "error",
            "message": message,
            "result": job_result
        }
        
        if success:
            results["summary"]["successful"] += 1
            print(f"\n✓ ip_locations.jsonl loaded successfully")
        else:
            results["summary"]["failed"] += 1
            print(f"\n✗ ip_locations.jsonl failed: {message}")
        
        # File 3: react_batch_combined_real.csv
        print("\n[File 3] Loading react_batch_combined_real.csv...")
        print("-" * 80)
        success, message, job_result = load_csv_to_bigquery(
            gcs_uri="gs://mongodb-0001/real-data/extracted/react_batch_combined_real.csv",
            dataset_id=dataset_id,
            table_id="react_batch_real",
            skip_leading_rows=1,
            autodetect_schema=True,
            write_disposition="WRITE_TRUNCATE"
        )
        
        results["files"]["react_batch_combined_real.csv"] = {
            "status": "success" if success else "error",
            "message": message,
            "result": job_result
        }
        
        if success:
            results["summary"]["successful"] += 1
            print(f"\n✓ react_batch_combined_real.csv loaded successfully")
        else:
            results["summary"]["failed"] += 1
            print(f"\n✗ react_batch_combined_real.csv failed: {message}")
        
        # Determine overall status
        if results["summary"]["failed"] == 0:
            results["status"] = "success"
        elif results["summary"]["successful"] > 0:
            results["status"] = "partial"
        else:
            results["status"] = "error"
        
        return results
    
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        print(f"✗ Unexpected error: {e}")
        return results
    
    finally:
        print("\n" + "=" * 80)
        print("BATCH LOAD COMPLETE")
        print("=" * 80)


def print_batch_summary(results: Dict[str, Any]):
    """Print formatted batch load summary."""
    print("\nBATCH LOAD SUMMARY")
    print("=" * 80)
    print(f"Status: {results['status'].upper()}")
    print(f"Successful: {results['summary']['successful']}/{results['summary']['total_files']}")
    print(f"Failed: {results['summary']['failed']}/{results['summary']['total_files']}")
    
    print("\nFile Details:")
    for file_name, file_result in results["files"].items():
        status = "✓" if file_result["status"] == "success" else "✗"
        print(f"\n  {status} {file_name}")
        print(f"    Status: {file_result['status'].upper()}")
        print(f"    Message: {file_result['message'][:70]}...")
        
        if file_result.get("result"):
            jr = file_result["result"]
            if "rows_loaded" in jr:
                print(f"    Rows Loaded: {jr['rows_loaded']:,}")
            if "table_ref" in jr:
                print(f"    Table: {jr['table_ref']}")
            if "job_id" in jr:
                print(f"    Job ID: {jr['job_id']}")


if __name__ == "__main__":
    # Run batch load
    results = batch_load_real_data(
        dataset_id="MongoDB_001",
        schema_file="./output/bigquery_schema.json"
    )
    
    # Print summary
    print_batch_summary(results)
    
    # Print final status
    print("\n" + "=" * 80)
    if results["status"] == "success":
        print("✓ ALL FILES LOADED SUCCESSFULLY!")
        print("\nYour BigQuery tables are now ready:")
        print("  - codealong-bq-491909.MongoDB_001.summary_data")
        print("  - codealong-bq-491909.MongoDB_001.ip_locations")
        print("  - codealong-bq-491909.MongoDB_001.react_batch_real")
    elif results["status"] == "partial":
        print("⚠️  PARTIAL SUCCESS - Some files loaded, some failed")
    else:
        print("✗ FAILED - Check error messages above")
    print("=" * 80)
