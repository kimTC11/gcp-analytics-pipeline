# IP Location & Product Data Processing Pipeline

**Professional MongoDB Data Processing Framework for Countly Analytics**

A comprehensive Python-based data pipeline to extract, enrich, and analyze IP locations and product information from 41.4M event records in MongoDB.

---

## 📋 Project Overview

This project implements a complete data processing pipeline with three main deliverables:

### ✅ Task 5: IP Location Processing - COMPLETED
- **Extracts**: 3.2M+ unique IP addresses from 41.4M event records
- **Enriches**: Adds geolocation data (country, region, city, coordinates)  
- **Outputs**: MongoDB collection + CSV file (150+ MB)
- **Status**: Successful | **Duration**: ~55 minutes

### ✅ Task 6: Product Information Collection - COMPLETED
- **Extracts**: 19,417 unique products from 7 event types
- **Processes**: 24M+ event documents
- **Outputs**: JSON (50+ MB) + CSV (2+ MB) formats
- **Status**: Successful | **Consolidation**: 99.1% valid names

### ✅ Task 7: React Data Extraction (Web Crawling) - COMPLETED
- **Crawls**: 19,417 product detail pages from Glamira
- **Success Rate**: 97.7% (18,969 succeeded, 448 failed)
- **Outputs**: 195 CSV files (5.8 MB) with extracted product data
- **Duration**: ~25 minutes | **Retry Logic**: 3+3 attempts with fallback URLs
- **Extracted Fields**: name, sku, price, product_type, gender, collection, currency, discounts

### ✅ Task 8: Documentation & Testing - COMPLETED
- **Setup Guide**: Complete installation instructions
- **Data Structure**: Detailed schema & field definitions
- **Execution Guides**: Step-by-step for all 7 tasks
- **Data Quality**: Automated verification & testing tools
- **Status**: Complete

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Setup
cd /home/tuancuong112504/prj5-gcp
python3 -m venv .venv
source .venv/bin/activate
pip install pymongo beautifulsoup4 requests IP2Location

# 2. Verify MongoDB
python3 << 'EOF'
from pymongo import MongoClient
MongoClient('mongodb://localhost:27017').admin.command('ping')
print("✓ MongoDB ready")
EOF

# 3. Run verification
python3 src/utils/data_quality_report.py
```

---

## 📁 Project Structure

```
prj5-gcp/
├── src/                                # Python source code
│   ├── core/
│   │   ├── ip_location_processor.py    # Task 5: IP extraction & enrichment
│   │   └── product_collector.py        # Task 6: Product extraction
│   ├── runners/
│   │   ├── run_ip_processing.py        # Task 5 main script
│   │   ├── run_product_collection.py   # Task 6 main script
│   │   └── run_full_crawl.py           # Task 7: Web crawling
│   ├── scripts/
│   │   ├── monitor_*.sh                # Monitoring scripts
│   │   └── run_*_nohup.sh             # Background execution
│   └── utils/
│       ├── data_quality_report.py      # Task 8: Data verification
│       └── verify_data_quality.py      # Quality checks
├── output/                              # Task 5-6 outputs
│   ├── products.csv                    # 19,417 products (Task 6)
│   ├── products.json                   # Product details (Task 6)
│   └── ip_locations.csv                # Enriched IP data (Task 5)
├── output_crawl/                        # Task 7 outputs
│   ├── react_batch_part_*.csv          # 195 success files (18,969 records)
│   └── react_batch_error_part_*.csv    # 86 error files (448 records)
├── logs/                                # Execution logs
│   ├── crawl.log                       # Task 7 web crawl log
│   ├── product_collection.log          # Task 6 log
│   └── ip_processing.log               # Task 5 log
├── docs/                                # Execution guides
│   ├── TASK5_EXECUTION_GUIDE.md        # IP location processing
│   ├── TASK6_EXECUTION_GUIDE.md        # Product collection
│   ├── TASK7_EXECUTION_GUIDE.md        # Web crawling (React data)
│   └── README.md
├── SETUP_INSTRUCTIONS.md               # Complete setup guide
├── DATA_STRUCTURE.md                   # Data format reference
└── README.md                           # This file
```

---

## 📊 Data Summary

### Task 5: IP Location Data
```
Unique IPs: 3,239,628
Countries: 195+
Output: output/ip_locations.csv (150-200 MB)
Fields: ip, country, region, city, latitude, longitude, isp, count, first/last_seen
Status: ✅ Complete
```

### Task 6: Product Information
```
Unique Products: 19,417
Valid Names: 19,241 (99.1%)
Output: output/products.csv (2 MB) + products.json (50 MB)
Fields: product_id, product_name, url, event_type, timestamp
Status: ✅ Complete
```

### Task 7: React Data (Web Crawled)
```
Crawled Products: 18,969 (97.7% success)
Failed Products: 448 (2.3%)
Output: output_crawl/ (5.8 MB across 281 files)
Fields: product_id, name, sku, price, product_type, gender, collection, discount-value
Success Files: 195 CSV files (100 records each)
Error Files: 86 CSV files (with error details)
Status: ✅ Complete
```

---

## 🔗 Execution Guides

- [Task 5: IP Location Processing](docs/TASK5_EXECUTION_GUIDE.md)
- [Task 6: Product Collection](docs/TASK6_EXECUTION_GUIDE.md)
- [Task 7: React Data Extraction](docs/TASK7_EXECUTION_GUIDE.md)

---

## 🛠 Running the Pipeline

### Task 5: IP Location Processing

```bash
source .venv/bin/activate
python3 src/runners/run_ip_processing.py

# Output: 
# ✓ 3,239,628 unique IPs extracted
# ✓ Geolocation data added
# ✓ Stored in MongoDB: countly.ip_locations
# ✓ CSV exported: log/ip_locations.csv
# Duration: ~30-60 minutes
```

### Task 6: Product Information Collection

```bash
source .venv/bin/activate
python3 src/runners/run_product_collection.py

# Output:
# ✓ 19,417 unique products identified
# ✓ Names consolidated
# ✓ JSON: output/products.json
# ✓ CSV: output/products.csv
# Duration: ~5-10 minutes
```

### Task 7: Data Quality Verification

```bash
source .venv/bin/activate

# Run comprehensive report
python3 src/utils/data_quality_report.py

# Run product test
python3 src/test/test_scrape.py
```

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** | Step-by-step installation & configuration |
| **[DATA_STRUCTURE.md](DATA_STRUCTURE.md)** | MongoDB schemas, CSV/JSON formats, field definitions |
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Alternative setup reference |

---

## 🔍 Output Files

### products.csv (2-3 MB)
```csv
product_id,product_name,url,event_type,timestamp
100001,glamira ring orva,https://glamira.ro/...,select_product_option_quality,1591224979
100002,glamira ring palmier,https://glamira.fr/...,select_product_option,1591261392
```

### products.json (50-70 MB)
```json
{
  "100001": {
    "product_id": "100001",
    "product_name": "Inel de Logodnă Orva",
    "url": "https://glamira.ro/glamira-ring-orva.html",
    "price": "6472.00",
    "collection": "halo"
  }
}
```

### ip_locations.csv (150-200 MB)
```csv
ip,country,region,city,latitude,longitude,isp,count,first_seen,last_seen
203.0.113.1,RO,Bucharest,Bucharest,44.4268,26.1025,ISP Name,1542,1591200000,1591300000
```

---

## 💻 System Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| **OS** | Ubuntu 18.04+ | Ubuntu 20.04+, Debian 11+ |
| **Python** | 3.10 | 3.11 |
| **MongoDB** | 4.4 | 5.0+ |
| **RAM** | 4 GB | 8+ GB |
| **Storage** | 60 GB | 100+ GB |
| **CPU** | 2 cores | 4+ cores |

---

## 🧪 Testing & Validation

### Verify Setup
```bash
source .venv/bin/activate

# Check MongoDB
python3 << 'EOF'
from pymongo import MongoClient
db = MongoClient()['countly']
print(f"Collections: {db.list_collection_names()}")
EOF

# Check output files
wc -l output/products.csv output/products.json
head -3 output/products.csv
```

### Run Tests
```bash
python3 src/utils/data_quality_report.py
python3 src/test/test_scrape.py
```

---

## 🐛 Troubleshooting

**MongoDB not running?**
```bash
sudo systemctl start mongod
sudo systemctl status mongod
```

**Python dependencies missing?**
```bash
source .venv/bin/activate
pip install pymongo beautifulsoup4 requests IP2Location
```

**Memory issues?**
- Reduce batch size: Edit `BATCH_SIZE = 500` in runner scripts
- Close other applications
- Monitor: `top`, `free -h`

For more details, see [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md#troubleshooting).

---

## 📋 Deliverables Checklist

- ✅ **Working VM with MongoDB** - 41.4M event records ready
- ✅ **Python scripts for IP processing** - Extract, enrich, export
- ✅ **Python scripts for product collection** - Extract, consolidate, export
- ✅ **Documentation**
  - Setup instructions with troubleshooting
  - Data structure & schema reference
  - Configuration & usage guide
- ✅ **Data Quality Verification**
  - Automated verification tools
  - Test suite with reports
  - Consistency validation

---

## 📞 Support

1. **Setup issues?** → [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)
2. **Data format questions?** → [DATA_STRUCTURE.md](DATA_STRUCTURE.md)
3. **Diagnostic tool** → `python3 src/utils/data_quality_report.py`
4. **MongoDB issues?** → `tail -f /var/log/mongodb/mongod.log`

---

**Ready to start?** → [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)

**Last Updated**: April 23, 2026  
**Project Status**: ✅ All Tasks Complete
