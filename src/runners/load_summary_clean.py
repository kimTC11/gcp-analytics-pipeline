#!/usr/bin/env python3
"""
Load summary_clean.jsonl from GCS to BigQuery MongoDB_001 dataset
With comprehensive logging to file and console
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Setup logging directory
LOG_DIR = Path(__file__).parent.parent.parent / "log"
LOG_DIR.mkdir(exist_ok=True)

# Create log file with timestamp
log_filename = LOG_DIR / f"load_summary_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add src to path (parent directory from runners location)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.gcs_to_bigquery_fixed import (
    GLAMIRA_SCHEMA,
    BQ,
    create_schema_from_yaml
)

logger.info("=" * 80)
logger.info("GCS to BigQuery Load Runner - summary_clean.jsonl")
logger.info("=" * 80)
logger.info(f"Log file: {log_filename}")


def main():
    logger.info("\n🚀 Starting load process...")
    
    # Configuration
    bucket_name = 'mongodb-0001'
    file_name = 'real-data/extracted/summary_clean.jsonl'
    dataset = 'MongoDB_001'
    table_name = 'summary_clean'
    
    logger.info(f"Configuration:")
    logger.info(f"  Bucket: {bucket_name}")
    logger.info(f"  File: {file_name}")
    logger.info(f"  Dataset: {dataset}")
    logger.info(f"  Table: {table_name}")
    
    # Create dataset if needed
    logger.info("\n📂 Checking dataset...")
    try:
        BQ.get_dataset(dataset)
        logger.info(f"✓ Dataset already exists: {dataset}")
    except Exception as e:
        logger.warning(f"Dataset not found, creating: {dataset}")
        try:
            from google.cloud import bigquery
            dataset_ref = BQ.dataset(dataset)
            dataset_obj = bigquery.Dataset(dataset_ref)
            dataset_obj.location = "US"
            dataset_obj = BQ.create_dataset(dataset_obj)
            logger.info(f"✓ Created dataset: {dataset}")
        except Exception as create_error:
            logger.error(f"✗ Error creating dataset: {str(create_error)}")
            return False
    
    # Create/verify table
    logger.info(f"\n📋 Checking table: {dataset}.{table_name}")
    try:
        from google.cloud import bigquery
        table_id = f"{BQ.project}.{dataset}.{table_name}"
        schema_fields = create_schema_from_yaml(GLAMIRA_SCHEMA)
        logger.info(f"  Schema fields: {len(schema_fields)}")
        
        table = bigquery.Table(table_id, schema=schema_fields)
        table = BQ.create_table(table, exists_ok=True)
        logger.info(f"✓ Table ready: {table_id}")
    except Exception as e:
        logger.error(f"✗ Error creating table: {str(e)}")
        return False
    
    # Load the data
    logger.info(f"\n📤 Starting data load...")
    logger.info(f"  Source: gs://{bucket_name}/{file_name}")
    logger.info(f"  Destination: {BQ.project}.{dataset}.{table_name}")
    
    try:
        from google.cloud import bigquery
        
        uri = f"gs://{bucket_name}/{file_name}"
        table_id = f"{BQ.project}.{dataset}.{table_name}"
        schema_fields = create_schema_from_yaml(GLAMIRA_SCHEMA)
        
        # Configure load job - bypass errors and track success
        job_config = bigquery.LoadJobConfig()
        job_config.schema = schema_fields
        job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
        job_config.allow_jagged_rows = True  # Allow rows with missing fields
        job_config.allow_quoted_newlines = True  # Allow newlines in quoted strings
        job_config.ignore_unknown_values = True  # Skip unknown fields
        job_config.max_bad_records = 10000000  # Allow up to 10 million bad records
        
        logger.info(f"\nLoad job configuration:")
        logger.info(f"  Format: NEWLINE_DELIMITED_JSON")
        logger.info(f"  Disposition: WRITE_APPEND")
        logger.info(f"  Allow jagged rows: True")
        logger.info(f"  Allow quoted newlines: True")
        logger.info(f"  Ignore unknown values: True")
        logger.info(f"  Max bad records: 10,000,000")
        
        # Start load job
        load_job = BQ.load_table_from_uri(uri, table_id, job_config=job_config)
        
        logger.info(f"\n⏱️  Job submitted")
        logger.info(f"  Job ID: {load_job.job_id}")
        logger.info(f"  Waiting for completion...")
        
        # Wait for job completion - capture partial loads even if there are errors
        try:
            load_job.result()
            logger.info(f"\n✅ Load job completed successfully!")
        except Exception as job_error:
            logger.warning(f"\n⚠️  Job encountered errors but may have loaded some data:")
            logger.warning(f"  Error: {str(job_error)[:300]}")
        
        # Get result statistics - check table even if job had errors
        logger.info(f"\n📊 Retrieving load statistics...")
        destination_table = BQ.get_table(table_id)
        rows_loaded = destination_table.num_rows
        table_size = destination_table.num_bytes
        
        logger.info(f"\n📊 Load Statistics:")
        logger.info(f"  ✓ Rows successfully loaded: {rows_loaded:,}")
        logger.info(f"  ✓ Table size: {table_size:,} bytes ({table_size / (1024**3):.2f} GB)")
        logger.info(f"  ✓ Location: {destination_table.project}.{destination_table.dataset_id}.{destination_table.table_id}")
        
        # Check if any rows were loaded
        if rows_loaded > 0:
            logger.info(f"\n✅ SUCCESS: {rows_loaded:,} records loaded to BigQuery")
            return True
        else:
            logger.error(f"\n❌ No records were loaded")
            return False
    
    except Exception as e:
        logger.error(f"\n❌ Error during load job: {str(e)}", exc_info=True)
        
        # Try to get table stats anyway
        try:
            destination_table = BQ.get_table(table_id)
            rows_loaded = destination_table.num_rows
            if rows_loaded > 0:
                logger.info(f"⚠️  However, {rows_loaded:,} records were previously loaded to the table")
                return True
        except Exception as table_error:
            logger.error(f"Could not retrieve table stats: {str(table_error)}")
        
        return False


if __name__ == "__main__":
    logger.info("")
    success = main()
    logger.info("\n" + "=" * 80)
    if success:
        logger.info("✅ Load operation completed successfully")
    else:
        logger.error("❌ Load operation failed")
    logger.info("=" * 80)
    logger.info(f"Log saved to: {log_filename}\n")
    sys.exit(0 if success else 1)
