import logging
import os
import json
import traceback
import re
from typing import Dict, List, Optional, Tuple, Any

from google.cloud import bigquery
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError, NotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load schema from JSON file
SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), '../../output/bigquery_schema.json')
GLAMIRA_SCHEMA = None

try:
    with open(SCHEMA_FILE_PATH) as f:
        GLAMIRA_SCHEMA = json.load(f)
    logger.info(f"✓ Loaded BigQuery schema from {SCHEMA_FILE_PATH}")
except FileNotFoundError:
    logger.error(f"Schema file not found: {SCHEMA_FILE_PATH}")
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON schema file: {str(e)}")

# Initialize GCP clients
PROJECT_ID = 'codealong-bq-491909'  # Your GCP Project ID
BQ_DATASET = 'staging'
DEFAULT_TABLE_NAME = 'glamira_products'

try:
    CS = storage.Client(project=PROJECT_ID)
    BQ = bigquery.Client(project=PROJECT_ID)
    logger.info(f"✓ Connected to GCP project: {PROJECT_ID}")
except Exception as e:
    logger.error(f"✗ Failed to initialize GCP clients: {str(e)}")
    CS = None
    BQ = None


def streaming(data: Dict[str, Any], table_name: str = DEFAULT_TABLE_NAME) -> bool:
    """
    Process a file event from Cloud Storage and load it to BigQuery.
    
    Args:
        data: Event data containing 'bucket' and 'name' (file path)
        table_name: BigQuery table name (default: glamira_products)
    
    Returns:
        True if processing successful, False otherwise
    """
    if not BQ or not CS:
        logger.error("GCP clients not initialized. Cannot process file.")
        return False
    
    if not GLAMIRA_SCHEMA:
        logger.error("Schema not loaded. Cannot process file.")
        return False
    
    try:
        bucket_name = data.get('bucket')
        file_name = data.get('name')
        time_created = data.get('timeCreated')
        
        logger.info(f"Processing file: gs://{bucket_name}/{file_name}")
        logger.info(f"Time Created: {time_created}")
        
        if not bucket_name or not file_name:
            logger.error("Invalid data: missing 'bucket' or 'name' fields")
            return False
        
        # Create table if it doesn't exist
        if not _check_if_table_exists(table_name, GLAMIRA_SCHEMA):
            logger.error(f"Failed to create/verify table: {table_name}")
            return False
        
        # Load data from GCS to BigQuery
        success = _load_table_from_uri(bucket_name, file_name, GLAMIRA_SCHEMA, table_name)
        return success
    
    except Exception as e:
        logger.error(f"Error streaming file. Cause: {traceback.format_exc()}")
        return False


def _check_if_table_exists(table_name: str, table_schema: List[Dict]) -> bool:
    """
    Check if table exists in BigQuery. Create if it doesn't.
    
    Args:
        table_name: The BigQuery table name
        table_schema: Schema definition from YAML config
    
    Returns:
        True if table exists or was created successfully, False otherwise
    """
    try:
        table_id = f"{BQ.project}.{BQ_DATASET}.{table_name}"
        
        try:
            existing_table = BQ.get_table(table_id)
            logger.info(f"✓ Table already exists: {table_id}")
            return True
        
        except NotFound:
            # Table doesn't exist, create it
            logger.info(f"Creating table: {table_name}")
            schema = create_schema_from_yaml(table_schema)
            table = bigquery.Table(table_id, schema=schema)
            created_table = BQ.create_table(table)
            logger.info(f"✓ Created table: {created_table.project}.{created_table.dataset_id}.{created_table.table_id}")
            return True
    
    except GoogleAPIError as e:
        logger.error(f"BigQuery error checking/creating table: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False


def _load_table_from_uri(bucket_name: str, file_name: str, table_schema: List[Dict], table_name: str) -> bool:
    """
    Load data from GCS to BigQuery table.
    
    Args:
        bucket_name: GCS bucket name
        file_name: File name in GCS
        table_schema: BigQuery schema from config
        table_name: Target BigQuery table name
    
    Returns:
        True if load successful, False otherwise
    """
    try:
        uri = f"gs://{bucket_name}/{file_name}"
        table_id = f"{BQ.project}.{BQ_DATASET}.{table_name}"
        
        logger.info(f"Loading file: {uri}")
        logger.info(f"Destination: {table_id}")
        
        # Create schema from YAML configuration
        schema = create_schema_from_yaml(table_schema)
        
        # Configure load job
        job_config = bigquery.LoadJobConfig()
        job_config.schema = schema
        job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
        job_config.allow_jagged_rows = True
        job_config.allow_quoted_newlines = True
        
        # Start load job
        load_job = BQ.load_table_from_uri(
            uri,
            table_id,
            job_config=job_config
        )
        
        logger.info(f"Load job started. Job ID: {load_job.job_id}")
        
        # Wait for job completion
        load_job.result()
        
        # Get result statistics
        destination_table = BQ.get_table(table_id)
        logger.info(f"✓ Data loaded successfully!")
        logger.info(f"  Total rows in table: {destination_table.num_rows:,}")
        logger.info(f"  Table size: {destination_table.num_bytes:,} bytes")
        
        return True
    
    except NotFound as e:
        logger.error(f"Dataset or table not found: {str(e)}")
        return False
    except GoogleAPIError as e:
        logger.error(f"BigQuery error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error loading data: {traceback.format_exc()}")
        return False


def create_schema_from_yaml(table_schema: List[Dict]) -> List[bigquery.SchemaField]:
    """
    Convert YAML schema definition to BigQuery SchemaField objects.
    Handles nested RECORD fields recursively.
    
    Args:
        table_schema: Schema definition from YAML config
    
    Returns:
        List of BigQuery SchemaField objects
    """
    schema = []
    
    for column in table_schema:
        name = column.get('name')
        field_type = column.get('type', 'STRING')
        mode = column.get('mode', 'NULLABLE')
        
        # Handle nested RECORD types
        if field_type == 'RECORD' and 'fields' in column:
            nested_fields = create_schema_from_yaml(column['fields'])
            schema_field = bigquery.SchemaField(
                name, 
                field_type, 
                mode=mode, 
                fields=tuple(nested_fields)
            )
        else:
            schema_field = bigquery.SchemaField(name, field_type, mode=mode)
        
        schema.append(schema_field)
    
    return schema


# Example usage (for testing - remove in production)
if __name__ == "__main__":
    print("=" * 80)
    print("GCS to BigQuery Event Processor")
    print("=" * 80)
    print("\nThis module is designed to be used as a Cloud Function.")
    print("In production, Google Cloud Platform will call the streaming() function")
    print("with event data when files are uploaded to Cloud Storage.")
    print("\nDo not call streaming(data) directly without proper event data.")
    print("=" * 80)
