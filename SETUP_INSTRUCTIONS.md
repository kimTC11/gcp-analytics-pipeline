# Setup Instructions - IP Location & Product Data Processing Pipeline

Complete step-by-step guide to set up and run the data processing pipeline.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Initial Setup](#initial-setup)
3. [MongoDB Setup](#mongodb-setup)
4. [Python Environment](#python-environment)
5. [Running the Pipeline](#running-the-pipeline)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum (8GB+ recommended for large datasets)
- **Storage**: 50GB+ for MongoDB, 2GB+ for output files
- **Network**: Internet for initial setup

### Software
- **OS**: Linux (Ubuntu 18.04+, Debian 10+) or macOS
- **Python**: 3.10 or 3.11
- **MongoDB**: 4.4+ (5.0+ recommended)
- **Bash**: 4.0+ (standard on most Linux systems)

### Network Access
- MongoDB accessible on `localhost:27017` or configured remote address
- Read/write permissions to project directories

---

## Initial Setup

### Step 1: Navigate to Project Directory

```bash
cd /home/tuancuong112504/prj5-gcp
```

### Step 2: Verify Project Structure

```bash
ls -la
```

Expected directories:
- `src/` - Python source code
- `output/` - Output CSV and JSON files
- `log/` - Processing logs
- `docs/` - Documentation
- `data/` - Data files (if any)

### Step 3: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Verify activation (prompt should show (.venv))
```

### Step 4: Install Python Dependencies

```bash
# Install required packages
pip install --upgrade pip setuptools wheel
pip install pymongo beautifulsoup4 requests IP2Location

# Or install from pyproject.toml if available
pip install -e .
```

Installed packages:
- **pymongo** - MongoDB driver for Python
- **beautifulsoup4** - HTML parsing
- **requests** - HTTP library
- **IP2Location** - IP geolocation database

---

## MongoDB Setup

### Step 1: Verify MongoDB Installation

```bash
# Check if MongoDB is running
mongosh --version

# Test connection
mongosh --eval "db.adminCommand('ping')"
```

### Step 2: Start MongoDB (if not running)

```bash
# On Linux
sudo systemctl start mongod

# Or using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Check status
sudo systemctl status mongod
```

### Step 3: Verify Database Connection from Python

```bash
python3 << 'EOF'
from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✓ MongoDB connection successful")
    
    # Check existing data
    db = client['countly']
    print(f"✓ Connected to 'countly' database")
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
EOF
```

---

## Python Environment

### Activate Virtual Environment

```bash
# Every time you open a new terminal
source .venv/bin/activate

# Verify activation
python3 --version  # Should show 3.10+
```

### Deactivate Virtual Environment

```bash
deactivate
```

### Check Installed Packages

```bash
pip list | grep -E "pymongo|beautifulsoup4|requests|IP2Location"
```

---

## Running the Pipeline

### Task 5: IP Location Processing

Extracts IP addresses from MongoDB and enriches them with geolocation data.

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run IP processing
python3 src/runners/run_ip_processing.py

# Monitor output
tail -f log/ip_processing.log  # If logging is enabled
```

**Output files:**
- `output/ip_locations.csv` - CSV format with IP and location data
- MongoDB collection: `ip_locations`

### Task 6: Product Information Collection

Extracts product data from MongoDB event collections.

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run product collection
python3 src/runners/run_product_collection.py

# Monitor output
tail -f log/product_collection.log
```

**Output files:**
- `output/products.csv` - Product data in CSV format
- `output/products.json` - Product data in JSON format

### Task 7: Data Quality Verification

Verify the integrity and quality of all processed data.

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run data quality verification
python3 src/utils/data_quality_report.py

# Or test products scraping
python3 src/test/test_scrape.py
```

---

## Verification & Testing

### Test MongoDB Connection

```bash
python3 << 'EOF'
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client['countly']

print("Collections in database:")
for collection in db.list_collection_names():
    count = db[collection].count_documents({})
    print(f"  - {collection}: {count:,} documents")
EOF
```

### Test Output Files

```bash
# Check CSV file
wc -l output/products.csv
head -5 output/products.csv

# Check JSON file
wc -l output/products.json
python3 -m json.tool output/products.json | head -20
```

### Run Data Quality Tests

```bash
source .venv/bin/activate
python3 src/utils/data_quality_report.py
```

---

## Quick Start Script

For convenience, use the provided quick start script:

```bash
bash quickstart.sh
```

This script handles:
- Virtual environment creation
- Dependency installation
- MongoDB connection verification
- Basic configuration

---

## Troubleshooting

### MongoDB Connection Issues

**Error**: "Connection refused" or "Unable to connect"

```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

### Python Import Errors

**Error**: "ModuleNotFoundError: No module named 'pymongo'"

```bash
# Verify virtual environment is activated
which python3  # Should show .venv/bin/python3

# Reinstall packages
pip install --upgrade pymongo beautifulsoup4 requests
```

### Permission Denied Errors

**Error**: "Permission denied" when accessing files

```bash
# Fix permissions
chmod -R 755 src/
chmod -R 755 output/

# Check ownership
ls -la output/
```

### Memory Issues

**Error**: "MemoryError" or process killed

- Reduce batch size in configuration
- Close other applications
- Increase available RAM
- Use MongoDB aggregation pipeline for large datasets

### Slow Performance

**Solution**: 
- Enable MongoDB indexing on frequently queried fields
- Check disk I/O performance (`iostat`)
- Monitor CPU usage (`top`)
- Consider parallel processing if available

---

## Configuration

### MongoDB URI

Default: `mongodb://localhost:27017`

To connect to remote MongoDB:

```python
MONGO_URI = "mongodb://user:password@host:port/database"
```

### Output Directory

Configure in your script:

```python
OUTPUT_DIR = Path(__file__).parent.parent / "output"
```

### Batch Size

Adjust for memory/performance:

```python
BATCH_SIZE = 1000  # Process 1000 records at a time
```

---

## Next Steps

1. ✅ Complete initial setup
2. ✅ Verify MongoDB connection
3. ✅ Run Task 5 (IP Processing)
4. ✅ Run Task 6 (Product Collection)
5. ✅ Run data quality verification
6. ✅ Review output files in `output/` directory

For more details, see [DATA_STRUCTURE.md](DATA_STRUCTURE.md).
