# GCS to BigQuery Data Loading

Complete setup for loading data from Google Cloud Storage (GCS) to BigQuery.

## 📋 Prerequisites

- Google Cloud Project with BigQuery and Cloud Storage enabled
- `gcloud` CLI installed and authenticated
- Python 3.9+
- GCP credentials configured (service account or Application Default Credentials)

## 🚀 Quick Start

### 1. Test Locally

Run the test suite to verify your configuration:

```bash
# Navigate to project root
cd /home/tuancuong112504/prj5-gcp

# Run tests
python3 test_gcs_to_bigquery.py
```

This will verify:
- ✓ Schema loading from JSON
- ✓ GCP authentication
- ✓ BigQuery connectivity
- ✓ Table creation
- ✓ Schema conversion

### 2. Deploy as Cloud Function

Deploy to Google Cloud Functions:

```bash
# Set your GCP project
export PROJECT_ID="codealong-bq-491909"
export BUCKET_NAME="mongodb-0001"  # The bucket that triggers the function
export REGION="us-central1"

# Deploy the function
gcloud functions deploy load_gcs_to_bigquery \
  --runtime python39 \
  --trigger-resource $BUCKET_NAME \
  --trigger-event google.storage.object.finalize \
  --entry-point load_gcs_to_bigquery \
  --source ./src \
  --project $PROJECT_ID \
  --region $REGION \
  --memory 512MB \
  --timeout 540s \
  --service-account default
```

### 3. Manual Upload to BigQuery

Load a specific file manually:

```python
from src.utils.gcs_to_bigquery_fixed import streaming

event_data = {
    'bucket': 'mongodb-0001',
    'name': 'real-data/extracted/react_batch_combined_real.jsonl',
    'timeCreated': '2026-05-10T10:00:00Z'
}

success = streaming(event_data, table_name='glamira_products')
print(f"Load {'succeeded' if success else 'failed'}")
```

## 📁 File Structure

```
src/
├── utils/
│   └── gcs_to_bigquery_fixed.py    # Core module with all loading functions
├── cloud_function.py               # Cloud Function entry point
└── __init__.py

output/
└── bigquery_schema.json            # Schema definition for glamira_products table

test_gcs_to_bigquery.py            # Test suite
```

## 🔧 Configuration

The module uses these settings (from `gcs_to_bigquery_fixed.py`):

```python
PROJECT_ID = 'codealong-bq-491909'      # Your GCP project
BQ_DATASET = 'staging'                  # Target dataset
DEFAULT_TABLE_NAME = 'glamira_products' # Target table
SCHEMA_FILE_PATH = '../../output/bigquery_schema.json'
```

### Customize

Edit `src/utils/gcs_to_bigquery_fixed.py` to change:

```python
# Line 31: Change GCP project
PROJECT_ID = 'your-project-id'

# Line 32: Change dataset
BQ_DATASET = 'your-dataset'

# Line 33: Change default table
DEFAULT_TABLE_NAME = 'your-table'
```

## 📊 Supported File Formats

- **JSONL** (Newline Delimited JSON) - `.jsonl`, `.ndjson`
- **CSV** - `.csv`

The module auto-detects format from file extension in `load_gcs_to_bigquery()`.

## 🔍 Monitoring

### View Cloud Function Logs

```bash
gcloud functions logs read load_gcs_to_bigquery \
  --project codealong-bq-491909 \
  --region us-central1 \
  --limit 50
```

### Check BigQuery Table Status

```bash
bq ls -t staging
bq show staging.glamira_products
bq head -20 staging.glamira_products
```

### Query Table

```bash
bq query --use_legacy_sql=false '
  SELECT COUNT(*) as row_count,
         COUNT(DISTINCT product_id) as unique_products
  FROM staging.glamira_products
'
```

## ⚠️ Troubleshooting

### "Schema file not found"
- Ensure `output/bigquery_schema.json` exists
- Check file path is relative to module location

### "BigQuery authentication error"
- Verify service account has `roles/bigquery.dataEditor`
- Run: `gcloud auth application-default login`
- Check: `gcloud config get-value project`

### "Dataset or table not found"
- Create dataset: `bq mk --dataset codealong-bq-491909:staging`
- Verify table creation permissions

### Job Timeout
- Increase Cloud Function timeout to 540s (default is 60s)
- Increase memory to 512MB or higher

## 📝 API Reference

### Main Function: `streaming()`

```python
def streaming(data: Dict[str, Any], table_name: str = 'glamira_products') -> bool:
    """
    Process a file event from Cloud Storage and load it to BigQuery.
    
    Args:
        data: Event data with keys: bucket, name, timeCreated
        table_name: BigQuery table name
    
    Returns:
        True if successful, False otherwise
    """
```

### Helper Functions

#### `_check_if_table_exists(table_name, table_schema)`
Creates BigQuery table if it doesn't exist.

#### `_load_table_from_uri(bucket_name, file_name, table_schema, table_name)`
Loads data from GCS to BigQuery using LoadJob.

#### `create_schema_from_yaml(table_schema)`
Converts JSON schema to BigQuery SchemaField objects.

## 🔐 Permissions Required

For the Cloud Function service account:

```bash
gcloud projects add-iam-policy-binding codealong-bq-491909 \
  --member serviceAccount:default@appspot.gserviceaccount.com \
  --role roles/bigquery.dataEditor

gcloud projects add-iam-policy-binding codealong-bq-491909 \
  --member serviceAccount:default@appspot.gserviceaccount.com \
  --role roles/storage.objectViewer
```

## 📚 Examples

### Load All Files from a Directory

```python
from google.cloud import storage
from src.utils.gcs_to_bigquery_fixed import streaming

storage_client = storage.Client()
bucket = storage_client.bucket('mongodb-0001')
blobs = bucket.list_blobs(prefix='real-data/extracted/')

for blob in blobs:
    if blob.name.endswith('.jsonl'):
        event_data = {
            'bucket': 'mongodb-0001',
            'name': blob.name,
            'timeCreated': blob.time_created.isoformat()
        }
        success = streaming(event_data)
        print(f"{blob.name}: {'✓' if success else '✗'}")
```

### Load with Custom Table Name

```python
event_data = {
    'bucket': 'mongodb-0001',
    'name': 'real-data/summary.jsonl'
}

success = streaming(event_data, table_name='my_custom_table')
```

## 🎯 Next Steps

1. **Test locally**: `python3 test_gcs_to_bigquery.py`
2. **Deploy**: Use the deployment command above
3. **Monitor**: Check logs in Cloud Console
4. **Query**: Use BigQuery console to analyze loaded data

---

**Last Updated**: May 10, 2026
**Project ID**: codealong-bq-491909
**Dataset**: staging
**Table**: glamira_products
