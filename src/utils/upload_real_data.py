"""
Real Data Upload to GCS

Complete workflow to combine real data files and upload to Google Cloud Storage
"""

import os
import json
import zipfile
import pandas as pd
from pathlib import Path
from glob import glob
from datetime import datetime
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError


#command to flatten the id in mongdb
# gcloud storage cat gs://mongodb-0001/real-data/extracted/summary.jsonl \
# | jq -c '._id = ._id["$oid"]' \
# | gcloud storage cp - gs://mongodb-0001/real-data/extracted/summary_clean.jsonl
# Copying file://- to gs://mongodb-0001/real-data/extracted/summary_clean.jsonl

def combine_success_crawl_files(
    input_dir: str = "./output_crawl",
    pattern: str = "react_batch_part_*.csv",
    output_file: str = "./output/react_batch_combined_real.csv"
) -> tuple[bool, str]:
    """
    Combine success crawl CSV files (react_batch_part_0001 to 0195).
    
    Args:
        input_dir: Directory containing react batch CSV files
        pattern: Glob pattern for files to combine
        output_file: Path to the combined output CSV file
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Find all react batch CSV files
        full_pattern = os.path.join(input_dir, pattern)
        csv_files = sorted(glob(full_pattern))
        
        if not csv_files:
            return False, f"No CSV files found in {input_dir} matching {pattern}"
        
        print(f"Found {len(csv_files)} CSV files to combine...")
        
        # Read and combine all CSV files
        dfs = []
        total_rows = 0
        
        for i, csv_file in enumerate(csv_files, 1):
            try:
                df = pd.read_csv(csv_file)
                dfs.append(df)
                total_rows += len(df)
                print(f"  [{i}/{len(csv_files)}] {os.path.basename(csv_file)}: {len(df):,} rows")
            except Exception as e:
                print(f"  ⚠️  Skipped {os.path.basename(csv_file)}: {str(e)}")
                continue
        
        if not dfs:
            return False, "No valid CSV files could be read"
        
        # Combine all dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save combined file
        combined_df.to_csv(output_file, index=False, encoding='utf-8')
        
        message = f"✓ Combined {len(csv_files)} files into {len(combined_df):,} rows → {output_file}"
        print(message)
        return True, message
    
    except Exception as e:
        error_msg = f"Error combining CSV files: {str(e)}"
        print(f"✗ {error_msg}")
        return False, error_msg


def create_zip_file(
    files_to_zip: list,
    zip_path: str = "./exports/real_data_export.zip"
) -> tuple[bool, str]:
    """
    Create a zip file containing the specified files.
    
    Args:
        files_to_zip: List of file paths to include in zip
        zip_path: Path for the output zip file
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Create zip directory if needed
        zip_dir = os.path.dirname(zip_path)
        if zip_dir:
            Path(zip_dir).mkdir(parents=True, exist_ok=True)
        
        print(f"\nCreating zip file: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_zip:
                if not os.path.exists(file_path):
                    print(f"  ⚠️  File not found: {file_path}")
                    continue
                
                # Use basename as arcname for cleaner zip structure
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname=arcname)
                
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size / 1024 / 1024 / 1024:.2f} GB" if file_size > 1024*1024*1024 else f"{file_size / 1024 / 1024:.2f} MB"
                print(f"  ✓ Added: {arcname} ({size_str})")
        
        zip_size = os.path.getsize(zip_path)
        size_str = f"{zip_size / 1024 / 1024 / 1024:.2f} GB" if zip_size > 1024*1024*1024 else f"{zip_size / 1024 / 1024:.2f} MB"
        message = f"✓ Zip file created successfully: {zip_path} ({size_str})"
        print(message)
        return True, message
    
    except Exception as e:
        error_msg = f"Error creating zip file: {str(e)}"
        print(f"✗ {error_msg}")
        return False, error_msg


def upload_to_gcs(
    file_path: str,
    bucket_name: str = "mongodb-0001",
    destination_blob_name: str = None
) -> tuple[bool, str]:
    """
    Upload a file to Google Cloud Storage.
    
    Args:
        file_path: Local file path to upload
        bucket_name: GCS bucket name (default: mongodb-0001)
        destination_blob_name: Name in GCS. If None, uses filename
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            print(f"✗ {error_msg}")
            return False, error_msg
        
        if destination_blob_name is None:
            destination_blob_name = os.path.basename(file_path)
        
        # Create GCS client
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        
        file_size = os.path.getsize(file_path)
        size_str = f"{file_size / 1024 / 1024 / 1024:.2f} GB" if file_size > 1024*1024*1024 else f"{file_size / 1024 / 1024:.2f} MB"
        
        print(f"\nUploading to GCS...")
        print(f"  File: {file_path}")
        print(f"  Size: {size_str}")
        print(f"  Bucket: {bucket_name}")
        print(f"  Destination: {destination_blob_name}")
        
        # Upload the file
        blob.upload_from_filename(file_path)
        
        message = f"✓ File uploaded successfully to gs://{bucket_name}/{destination_blob_name}"
        print(message)
        return True, message
    
    except GoogleAPIError as e:
        error_msg = f"GCS upload error: {str(e)}"
        print(f"✗ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error during upload: {str(e)}"
        print(f"✗ {error_msg}")
        return False, error_msg


def upload_real_data_workflow() -> dict:
    """
    Complete workflow for real data upload:
    1. Combine react_batch_part_0001 to 0195 CSV files
    2. Create zip with:
       - exports/ip_locations_20260506_105815.jsonl
       - summary.jsonl
       - combined react_batch CSV
    3. Upload to GCS
    
    Returns:
        Dictionary with workflow results
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"real_data_export_{timestamp}.zip"
    zip_path = f"./exports/{zip_filename}"
    combined_csv_path = "./output/react_batch_combined_real.csv"
    
    results = {
        "status": "in_progress",
        "steps": {},
        "timestamp": timestamp
    }
    
    try:
        print("=" * 80)
        print("WORKFLOW: Real Data Upload to GCS")
        print("=" * 80)
        
        # Step 1: Combine React batch CSV files (success crawl only)
        print("\n[Step 1] Combining react_batch_part CSV files (0001-0195)...")
        print("-" * 80)
        success, message = combine_success_crawl_files()
        results["steps"]["combine_csv"] = {"success": success, "message": message}
        
        if not success:
            results["status"] = "error"
            results["error"] = "Failed to combine CSV files"
            return results
        
        # Step 2: Prepare files for zipping
        print("\n[Step 2] Preparing files for zipping...")
        print("-" * 80)
        
        files_to_zip = [
            "./exports/ip_locations_20260506_105815.jsonl",
            "./summary.jsonl",
            combined_csv_path
        ]
        
        print(f"Files to zip ({len(files_to_zip)} total):")
        for f in files_to_zip:
            if os.path.exists(f):
                size = os.path.getsize(f)
                size_str = f"{size / 1024 / 1024 / 1024:.2f} GB" if size > 1024*1024*1024 else f"{size / 1024 / 1024:.2f} MB"
                print(f"  ✓ {f} ({size_str})")
            else:
                print(f"  ✗ {f} (not found)")
        
        # Step 3: Create zip file
        print("\n[Step 3] Creating zip file...")
        print("-" * 80)
        success, message = create_zip_file(files_to_zip, zip_path)
        results["steps"]["create_zip"] = {"success": success, "message": message}
        
        if not success:
            results["status"] = "error"
            results["error"] = "Failed to create zip file"
            return results
        
        # Step 4: Upload to GCS
        print("\n[Step 4] Uploading to Google Cloud Storage...")
        print("-" * 80)
        success, message = upload_to_gcs(
            file_path=zip_path,
            bucket_name="mongodb-0001",
            destination_blob_name=f"real-data/{zip_filename}"
        )
        results["steps"]["upload_gcs"] = {"success": success, "message": message}
        
        if success:
            results["status"] = "success"
            results["zip_file"] = zip_path
            results["gcs_path"] = f"gs://mongodb-0001/real-data/{zip_filename}"
        else:
            results["status"] = "partial"
            results["error"] = "Zip created but upload failed"
        
        return results
    
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        return results
    
    finally:
        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    # Run the complete workflow
    result = upload_real_data_workflow()
    
    # Print summary
    print("\nSUMMARY:")
    print(f"Status: {result['status'].upper()}")
    for step, details in result["steps"].items():
        status = "✓" if details["success"] else "✗"
        msg = details['message'][:80] if len(details['message']) > 80 else details['message']
        print(f"  {status} {step}: {msg}")
    
    if result["status"] == "success":
        print(f"\n✓ Upload successful!")
        print(f"  GCS Path: {result['gcs_path']}")
    elif result.get("error"):
        print(f"\n✗ Error: {result['error']}")
