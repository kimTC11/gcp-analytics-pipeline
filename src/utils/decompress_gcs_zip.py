"""
GCS Zip Decompression Utility

Decompress zip files from Google Cloud Storage
"""

import os
import zipfile
import tempfile
from pathlib import Path
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError


def decompress_gcs_zip(
    bucket_name: str = "mongodb-0001",
    zip_blob_path: str = "real-data/real_data_export_20260506_115124.zip",
    extract_to_gcs: bool = True,
    gcs_extract_dir: str = "real-data/extracted/",
    local_extract_dir: str = "./extracted_data/"
) -> dict:
    """
    Download and decompress a zip file from GCS.
    
    Args:
        bucket_name: GCS bucket name
        zip_blob_path: Path to zip file in GCS (e.g., real-data/file.zip)
        extract_to_gcs: If True, upload extracted files back to GCS
        gcs_extract_dir: Directory in GCS to upload extracted files
        local_extract_dir: Local directory to extract files
    
    Returns:
        Dictionary with decompression results
    
    Example:
        result = decompress_gcs_zip(
            bucket_name="mongodb-0001",
            zip_blob_path="real-data/real_data_export_20260506_115124.zip"
        )
        if result["status"] == "success":
            print(f"Extracted {len(result['files'])} files")
    """
    results = {
        "status": "in_progress",
        "bucket": bucket_name,
        "zip_file": zip_blob_path,
        "files": [],
        "extracted_count": 0,
        "uploaded_count": 0
    }
    
    try:
        # Create local extraction directory
        extract_dir = Path(local_extract_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Create GCS client
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(zip_blob_path)
        
        print(f"Downloading zip file from GCS...")
        print(f"  Bucket: {bucket_name}")
        print(f"  File: {zip_blob_path}")
        
        # Download zip file to temp location
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            blob.download_to_filename(tmp_path)
            print(f"✓ Downloaded to: {tmp_path}")
        
        # Extract zip file
        print(f"\nExtracting zip file...")
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # List extracted files
        extracted_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                extracted_files.append(file)
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size / 1024 / 1024 / 1024:.2f} GB" if file_size > 1024*1024*1024 else f"{file_size / 1024 / 1024:.2f} MB"
                print(f"  ✓ {file} ({size_str})")
        
        results["extracted_count"] = len(extracted_files)
        results["files"] = extracted_files
        
        # Clean up temp file
        os.remove(tmp_path)
        print(f"✓ Extracted {len(extracted_files)} files to {extract_dir}")
        
        # Upload extracted files back to GCS if requested
        if extract_to_gcs and extracted_files:
            print(f"\nUploading extracted files to GCS...")
            print(f"  Target directory: gs://{bucket_name}/{gcs_extract_dir}")
            
            for file in extracted_files:
                file_path = extract_dir / file
                gcs_blob_name = f"{gcs_extract_dir}{file}"
                gcs_blob = bucket.blob(gcs_blob_name)
                
                print(f"  Uploading: {file}...", end=" ", flush=True)
                gcs_blob.upload_from_filename(str(file_path))
                
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size / 1024 / 1024 / 1024:.2f} GB" if file_size > 1024*1024*1024 else f"{file_size / 1024 / 1024:.2f} MB"
                print(f"✓ ({size_str})")
                
                results["uploaded_count"] += 1
        
        results["status"] = "success"
        results["local_path"] = str(extract_dir)
        results["gcs_path"] = f"gs://{bucket_name}/{gcs_extract_dir}" if extract_to_gcs else None
        
        return results
    
    except GoogleAPIError as e:
        results["status"] = "error"
        results["error"] = f"GCS error: {str(e)}"
        print(f"✗ GCS error: {e}")
        return results
    
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        print(f"✗ Error: {e}")
        return results


if __name__ == "__main__":
    print("=" * 80)
    print("GCS Zip Decompression Utility")
    print("=" * 80)
    
    # Decompress the real data zip file
    result = decompress_gcs_zip(
        bucket_name="mongodb-0001",
        zip_blob_path="real-data/real_data_export_20260506_115124.zip",
        extract_to_gcs=True,
        gcs_extract_dir="real-data/extracted/"
    )
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Status: {result['status'].upper()}")
    print(f"Extracted files: {result['extracted_count']}")
    print(f"Uploaded to GCS: {result['uploaded_count']}")
    print(f"Local path: {result.get('local_path', 'N/A')}")
    if result.get('gcs_path'):
        print(f"GCS path: {result['gcs_path']}")
    
    if result["status"] == "success":
        print(f"\n✓ Decompression successful!")
        print(f"Files extracted:")
        for file in result["files"]:
            print(f"  - {file}")
    else:
        print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
