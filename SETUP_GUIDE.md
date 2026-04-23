# Setup Guide - Complete Installation Instructions

Comprehensive step-by-step guide for setting up the IP Location & Product Data Processing Pipeline.

---

## 📋 Table of Contents

1. [System Requirements](#-system-requirements)
2. [Initial Setup](#-initial-setup)
3. [MongoDB Setup](#-mongodb-setup)
4. [Python Environment](#-python-environment)
5. [IP2Location Database](#-ip2location-database)
6. [Verification](#-verification)
7. [Troubleshooting](#-troubleshooting)

---

## ✅ System Requirements

### Hardware
- **CPU**: 2+ cores (4+ recommended for optimal performance)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 
  - MongoDB: 50GB+ (41.4M documents × ~800 bytes)
  - IP2Location: 500MB+
  - Output: 2GB+ (CSV files)

### Software
- **OS**: Linux (Ubuntu 18.04+, Debian 10+) or macOS
- **Python**: 3.10 or 3.11
- **MongoDB**: 4.4+ (5.0+ recommended)
- **Bash**: 4.0+ (built-in on most systems)

### Network
- MongoDB accessible on `localhost:27017` (or configured remote)
- Internet connection for initial setup (not required for processing)

---

## 🚀 Initial Setup

### Step 1: Clone/Download Project

```bash
# Navigate to your projects directory
cd /home/tuancuong112504/prj5-gcp

# Verify project structure exists
ls -la
# Expected output:
# drwxr-xr-x log/
# drwxr-xr-x mongodb-data/
# drwxr-xr-x output/
# drwxr-xr-x source/
# -rw-r--r-- README.md
```

### Step 2: Create Project Structure (if missing)

```bash
cd /home/tuancuong112504/prj5-gcp

# Create necessary directories
mkdir -p log
mkdir -p output
mkdir -p monggodb-data

# Verify structure
tree -L 1
# or: ls -la
```

---

## 🗄️ MongoDB Setup

### Option 1: Local MongoDB (Recommended for Development)

#### Install MongoDB (Ubuntu/Debian)
```bash
# Update package manager
sudo apt update

# Install MongoDB
sudo apt install -y mongodb

# Start MongoDB service
sudo systemctl start mongodb
sudo systemctl enable mongodb  # Auto-start on reboot

# Verify installation
mongosh --version
# or: mongo --version
```

#### Install MongoDB (macOS)
```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community

# Verify
mongosh --version
```

#### Install MongoDB (Docker - Alternative)
```bash
# Run MongoDB in Docker
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:5.0

# Verify connection
docker exec -it mongodb mongosh

# Stop container
docker stop mongodb
```

### Option 2: Remote MongoDB

If using a remote MongoDB instance:

1. Update connection string in Python scripts:
   ```python
   MONGO_URI = "mongodb://username:password@host:port"
   ```

2. Ensure network connectivity:
   ```bash
   # Test connection
   mongosh mongodb://host:port
   ```

### Step 3: Verify MongoDB Connection

```bash
# Connect to MongoDB shell
mongosh

# In the mongo shell:
> db.adminCommand('ping')
{ ok: 1 }

# Check existing databases
> show dbs

# Exit
> exit
```

### Step 4: Prepare MongoDB Data

**If data already exists:**
```bash
# In mongosh, switch to countly database
> use countly

# Check collections
> show collections

# Count documents in summary
> db.summary.countDocuments()
# Should show 41.4M+ documents
```

**If data needs to be imported:**
```bash
# Import from MongoDB dump (if available)
mongorestore --uri="mongodb://localhost:27017" /path/to/dump

# or import from JSON/CSV
mongoimport --uri="mongodb://localhost:27017/countly" \
  --collection=summary \
  --file=data.json
```

---

## 🐍 Python Environment

### Step 1: Verify Python Installation

```bash
# Check Python version (3.10+ required)
python3 --version
# Output: Python 3.11.0

# Check pip
pip3 --version
```

### Step 2: Create Virtual Environment

```bash
cd /home/tuancuong112504/prj5-gcp

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# You should see (.venv) in your prompt
# Example: (.venv) user@host:~/prj5-gcp$
```

### Step 3: Install Dependencies

```bash
# Navigate to source directory
cd source

# Install from pyproject.toml
pip install -r pyproject.toml

# Or install packages individually
pip install pymongo==4.3.3
pip install ip2location==8.10.0
pip install python-dotenv==0.21.0

# Verify installations
pip list
```

### Step 4: Verify Dependencies

```bash
# Test Python imports
python3 -c "import pymongo; print('✓ pymongo')"
python3 -c "import IP2Location; print('✓ IP2Location')"
python3 -c "import csv; print('✓ csv')"
python3 -c "import json; print('✓ json')"

# All should print ✓ with module name
```

---

## 🌍 IP2Location Database

### Step 1: Obtain IP2Location Database

The IP2Location BIN database is required for IP geolocation.

#### Option A: Download from IP2Location (Recommended)
1. Visit [ip2location.com](https://www.ip2location.com/download/)
2. Download "**IP-COUNTRY-REGION-CITY.BIN**" file
3. Place in `/home/tuancuong112504/prj5-gcp/monggodb-data/`

#### Option B: Use Free Alternative
```bash
# GeoLite2 database (free alternative)
cd /home/tuancuong112504/prj5-gcp/monggodb-data/

# Download GeoLite2-City.tar.gz
wget https://github.com/maxmind/GeoipDB/releases/download/2023-06/GeoLite2-City.tar.gz

tar -xzf GeoLite2-City.tar.gz

# Note: Requires code modification in ip_location_processor.py
```

### Step 2: Verify Database File

```bash
# Check file exists and size
ls -lh /home/tuancuong112504/prj5-gcp/monggodb-data/IP-COUNTRY-REGION-CITY.BIN

# Expected output (example):
# -rw-r--r-- 1 user group 450M Apr 22 10:00 IP-COUNTRY-REGION-CITY.BIN
```

### Step 3: Update Path in Code (if needed)

If your IP2Location file is in a different location, update the path:

```python
# In source/ip_location_processor.py
DB_PATH = "/your/custom/path/IP-COUNTRY-REGION-CITY.BIN"
```

---

## ✅ Verification

### Comprehensive Setup Test

Run the verification script:

```bash
cd /home/tuancuong112504/prj5-gcp/source

# Activate virtual environment
source ../.venv/bin/activate

# Run setup test
python test_setup.py
```

**Expected output:**
```
✓ Python version: 3.11.0
✓ MongoDB connection: OK
✓ Database 'countly' exists
✓ Collection 'summary' exists
✓ IP2Location database: OK
✓ Output directory: writable
✓ Log directory: writable
✓ Virtual environment: active

All checks passed! Setup is complete.
```

### Manual Verification Steps

#### 1. Test MongoDB Connection
```bash
# In mongosh
> use countly
> db.summary.countDocuments()
# Should return ~41.4M
```

#### 2. Test Python Environment
```bash
python3 << 'EOF'
import sys
print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")

from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
print(f"MongoDB: Connected")
client.close()

import IP2Location
print("IP2Location: Ready")
EOF
```

#### 3. Test File Paths
```bash
# Verify all critical paths
test -d /home/tuancuong112504/prj5-gcp/log && echo "✓ log/" || echo "✗ log/"
test -d /home/tuancuong112504/prj5-gcp/output && echo "✓ output/" || echo "✗ output/"
test -f /home/tuancuong112504/prj5-gcp/monggodb-data/IP-COUNTRY-REGION-CITY.BIN && echo "✓ IP2Location" || echo "✗ IP2Location"
test -f /home/tuancuong112504/prj5-gcp/.venv/bin/python && echo "✓ venv" || echo "✗ venv"
```

---

## 🔧 Troubleshooting

### MongoDB Connection Issues

**Problem: "Connection refused"**
```bash
# Check if MongoDB is running
sudo systemctl status mongodb

# Start MongoDB if not running
sudo systemctl start mongodb

# Or check port
netstat -tuln | grep 27017
```

**Problem: "Authentication failed"**
```bash
# If using authentication, verify credentials
mongosh mongodb://username:password@localhost:27017

# Or connect without auth (if enabled)
mongosh mongodb://localhost:27017
```

### Python/Package Issues

**Problem: "ModuleNotFoundError: No module named 'pymongo'"**
```bash
# Verify virtual environment is activated
which python
# Should show: /home/tuancuong112504/prj5-gcp/.venv/bin/python

# Reinstall packages
pip install --upgrade pymongo
```

**Problem: "Permission denied" on database file**
```bash
# Fix permissions
chmod 644 /home/tuancuong112504/prj5-gcp/monggodb-data/IP-COUNTRY-REGION-CITY.BIN

# Verify
ls -l /home/tuancuong112504/prj5-gcp/monggodb-data/IP-COUNTRY-REGION-CITY.BIN
```

### Disk Space Issues

**Check available space:**
```bash
# Check disk usage
df -h /home/tuancuong112504/prj5-gcp

# Check MongoDB data size
du -sh /var/lib/mongodb

# Check project size
du -sh /home/tuancuong112504/prj5-gcp
```

### Performance Issues

**Optimize MongoDB:**
```bash
# In mongosh
> db.summary.createIndex({ip: 1})
> db.summary.createIndex({collection: 1})

# Verify indexes
> db.summary.getIndexes()
```

**Monitor system resources:**
```bash
# Real-time monitoring
top -b -n 1 | head -20

# Memory usage
free -h

# CPU usage
nproc
```

---

## 📊 Post-Setup Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] MongoDB running and accessible
- [ ] MongoDB contains countly.summary collection (41.4M+ documents)
- [ ] All Python packages installed (pymongo, ip2location)
- [ ] IP2Location BIN database present (~450MB)
- [ ] `/log` directory writable
- [ ] `/output` directory writable
- [ ] `test_setup.py` passes all checks
- [ ] MongoDB connection test successful

---

## 🎯 Next Steps

After setup is complete:

1. **Run Task 5 (IP Processing):**
   ```bash
   cd /home/tuancuong112504/prj5-gcp/source
   bash run_with_nohup.sh
   ```

2. **Monitor Progress:**
   ```bash
   bash monitor_progress.sh
   ```

3. **Verify Output:**
   ```bash
   # Check logs
   tail -f ../log/ip_processing.log
   
   # Check MongoDB
   mongosh
   > use countly
   > db.ip_locations.countDocuments()
   
   # Check CSV
   head ../output/ip_locations.csv
   ```

4. **Proceed to Task 6:** See [TASK6_EXECUTION_GUIDE.md](TASK6_EXECUTION_GUIDE.md)

---

**Setup Complete!** You're ready to run the data processing pipeline.
