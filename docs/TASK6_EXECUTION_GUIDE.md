# Task 6: Product Information Collection - Execution Guide

## Overview

Extracts and processes product information from 41.4M event records in MongoDB.

**Duration:** 1-2 hours
**Processing:** Filters events by type, extracts product IDs and URLs, derives product names

---

## Quick Start (Run in Background)

### 1️⃣  Start Processing with nohup

```bash
cd /home/tuancuong112504/prj5-gcp/source
bash run_product_with_nohup.sh
```

This will:
- ✓ Start the processing in the background
- ✓ Show the process ID (PID)
- ✓ Create a log file: `product_collection.log`
- ✓ Display the first logs

### 2️⃣  Monitor Progress in Real-Time

```bash
bash monitor_products.sh
```

Or manually:

```bash
tail -f product_collection.log
```

---

## Available Scripts

### `product_collector.py` (Main Module)

Core module containing the `ProductCollector` class.

### `run_product_collection.py` (Runner)

Direct execution (runs in foreground):

```bash
cd /home/tuancuong112504/prj5-gcp/source
source .venv/bin/activate
python run_product_collection.py
```

### `run_product_with_nohup.sh` (Background Execution)

Runs the processor in background with nohup:

```bash
bash run_product_with_nohup.sh
```

**Benefits:**
- Process continues even if you disconnect SSH
- Real-time logging to `product_collection.log`
- Shows process PID for monitoring

### `monitor_products.sh` (Real-Time Monitoring)

Follow the log file live:

```bash
bash monitor_products.sh
```

Press `Ctrl+C` to stop monitoring (process keeps running).

---

## Processing Stages & Timeline

### Stage 1: MongoDB Connection
- **Duration:** 2-5 seconds
- **What:** Connecting to MongoDB
- **Log Output:** `✓ Connected to MongoDB`

### Stage 2: Event Filtering & Data Extraction
- **Duration:** 30 minutes - 1+ hour
- **What:** Scanning 41.4M records, filtering by event type, extracting product IDs and URLs
- **Event Types Processed:**
  - view_product_detail
  - select_product_option
  - select_product_option_quality
  - add_to_cart_action
  - product_detail_recommendation_visible
  - product_detail_recommendation_noticed
  - product_view_all_recommend_clicked
- **Log Output:** Progress every 100,000 records
- **Example:** `Progress: 100,000 records processed | 45,000 unique products found`

### Stage 3: Product Name Extraction
- **Duration:** 10-30 minutes
- **What:** Parsing URLs to extract product names
- **Log Output:** Progress every 100,000 products
- **Example:** `Progress: 100,000/200,000 | Success: 95,000 | Failed: 5,000`

### Stage 4: File Output
- **Duration:** 1-5 minutes
- **What:** Writing JSON and CSV files
- **Log Output:** File paths

---

## Log Output Examples

### Successful Start

```
[2026-04-22 10:15:30] ================================================================================
[2026-04-22 10:15:30] TASK 6: Product Information Collection
[2026-04-22 10:15:30] ================================================================================
[2026-04-22 10:15:30] 
[2026-04-22 10:15:30] ⚠️  This task extracts product data from 41.4M event records
[2026-04-22 10:15:30] ⏱️  EXPECTED DURATION: 1-2 hours depending on system resources
[2026-04-22 10:15:32] [1] Connecting to MongoDB...
[2026-04-22 10:15:33] ✓ Connected to MongoDB: mongodb://localhost:27017
[2026-04-22 10:15:33] 
[2026-04-22 10:15:33] [2] Processing product information...
[2026-04-22 10:15:33]     Filtering events and extracting URLs...
[2026-04-22 10:15:33]     Extracting product names from URLs...
```

### During Processing

```
[2026-04-22 10:45:00]   Progress: 100,000 records processed | 45,000 unique products found
[2026-04-22 10:50:00]   Progress: 200,000 records processed | 85,000 unique products found
[2026-04-22 11:15:00]   Progress: 500,000 records processed | 180,000 unique products found
[2026-04-22 11:45:00] ✓ Extraction complete:
[2026-04-22 11:45:00]   Total records processed: 1,500,000
[2026-04-22 11:45:00]   Unique products found: 320,000
[2026-04-22 11:45:01] 
[2026-04-22 11:45:01] Extracting product names from URLs...
[2026-04-22 11:50:00]   Progress: 100,000/320,000 | Success: 95,000 | Failed: 5,000
[2026-04-22 11:55:00]   Progress: 200,000/320,000 | Success: 190,000 | Failed: 10,000
```

### Completion

```
[2026-04-22 12:30:00] ✓ Name extraction complete:
[2026-04-22 12:30:00]   Successfully extracted: 300,000
[2026-04-22 12:30:00]   Failed to extract: 20,000
[2026-04-22 12:30:05] ✓ JSON file saved: /home/tuancuong112504/prj5-gcp/output/products.json
[2026-04-22 12:30:06] ✓ CSV file saved: /home/tuancuong112504/prj5-gcp/output/products.csv
[2026-04-22 12:30:06] 
[2026-04-22 12:30:06] ================================================================================
[2026-04-22 12:30:06] ✅ PROCESSING COMPLETE
[2026-04-22 12:30:06] ================================================================================
[2026-04-22 12:30:06] Status: completed
[2026-04-22 12:30:06] Total products extracted: 320,000
[2026-04-22 12:30:06]   ✓ With product name: 300,000
[2026-04-22 12:30:06]   ✗ Without product name: 20,000
[2026-04-22 12:30:06] 
[2026-04-22 12:30:06] Output files:
[2026-04-22 12:30:06]   JSON: /home/tuancuong112504/prj5-gcp/output/products.json
[2026-04-22 12:30:06]   CSV: /home/tuancuong112504/prj5-gcp/output/products.csv
[2026-04-22 12:30:06] 
[2026-04-22 12:30:06] ⏱️  Timing:
[2026-04-22 12:30:06]   Processing Duration: 75.2 minutes (1.25 hours)
[2026-04-22 12:30:06]   Total Duration: 75.3 minutes (1.25 hours)
[2026-04-22 12:30:06] ================================================================================
```

---

## Monitoring & Management

### Check Process Status

```bash
# Get process ID and status
ps -p <PID>

# Or search for the process
ps aux | grep "product_collection"
```

### View Last 100 Lines of Log

```bash
tail -100 product_collection.log
```

### View Last 50 Lines and Follow

```bash
tail -f -n 50 product_collection.log
```

### Count Progress (Records processed so far)

```bash
grep "Progress:" product_collection.log | tail -5
```

### Kill Process (if needed)

```bash
# Replace <PID> with the actual process ID
kill <PID>

# Force kill if needed
kill -9 <PID>
```

---

## Output Files

### JSON Output

**Location:** `/home/tuancuong112504/prj5-gcp/output/products.json`

**Format:**
```json
{
  "product_123": {
    "product_id": "product_123",
    "product_name": "diamond ring",
    "url": "https://example.com/product/diamond-ring",
    "event_type": "view_product_detail",
    "timestamp": 1619000000
  },
  "product_456": {
    ...
  }
}
```

**Usage:** For detailed product information, data transformations, or API uploads

### CSV Output

**Location:** `/home/tuancuong112504/prj5-gcp/output/products.csv`

**Format:**
```
product_id,product_name,url,event_type,timestamp
product_123,diamond ring,https://example.com/product/diamond-ring,view_product_detail,1619000000
product_456,gold necklace,https://example.com/product/gold-necklace,add_to_cart_action,1619000100
```

**Usage:** For spreadsheet analysis, loading into databases, or reporting

---

## Troubleshooting

### Log File Not Updating

1. Check if process is still running:
   ```bash
   ps aux | grep "product_collection"
   ```

2. The process might be in URL parsing (slower stage). Wait longer.

3. Check for errors:
   ```bash
   tail -50 product_collection.log | grep -i "error"
   ```

### MongoDB Connection Failed

Verify MongoDB is running:

```bash
mongosh --eval "db.adminCommand('ping')"
```

### Process Takes Too Long

- This is normal for 41.4M records
- Check current progress with `tail -f product_collection.log`
- Event filtering can take 30 min - 1 hour
- Patient waiting is required

### Memory Issues

The process may consume 2-4 GB RAM. You can:

1. Monitor RAM usage:
   ```bash
   ps aux | grep product_collection
   ```

2. Stop other processes to free resources

3. Restart and try again

---

## Expected Results

| Metric | Expected Value |
|--------|-----------------|
| Total Records Scanned | 41.4M |
| Unique Products | 100K - 500K |
| Products with Names | 90% - 95% |
| Processing Duration | 1-2 hours |
| JSON File Size | 10-100 MB |
| CSV File Size | 5-50 MB |

---

## Success Checklist

- [ ] Start process with `bash run_product_with_nohup.sh`
- [ ] Monitor with `bash monitor_products.sh` or `tail -f product_collection.log`
- [ ] Watch for progress updates every 100,000 records
- [ ] Wait for "✅ PROCESSING COMPLETE" message
- [ ] Verify output files exist:
  - [ ] `output/products.json`
  - [ ] `output/products.csv`
- [ ] Check statistics (total, with names, without names)
- [ ] Review sample data in JSON or CSV files

---

## Next Steps After Completion

1. **Data Quality Check:**
   ```bash
   # Check JSON file
   head -20 output/products.json
   
   # Count products in CSV
   wc -l output/products.csv
   ```

2. **Integration:**
   - Import CSV into analysis tool
   - Load JSON for API consumption
   - Use for product catalog enrichment

3. **Next Tasks:**
   - Task 7, 8, etc.

---

**Good luck with product collection! 🚀**
