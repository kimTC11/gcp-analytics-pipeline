# Task 5: IP Location Processing - Execution Guide

## Overview

This guide explains how to run the IP location processing script for your large MongoDB dataset (41.4M documents, 34GB).

**Estimated Duration:** 2-6 hours depending on system resources

---

## Quick Start (Run in Background)

### 1️⃣  Start Processing with nohup

```bash
cd /home/tuancuong112504/prj5-gcp/source
bash run_with_nohup.sh
```

This will:
- ✓ Start the processing in the background
- ✓ Show the process ID (PID)
- ✓ Create a log file: `ip_processing.log`
- ✓ Display the first logs

### 2️⃣  Monitor Progress in Real-Time

```bash
bash monitor_progress.sh
```

Or manually:

```bash
tail -f ip_processing.log
```

---

## Available Scripts

### `run_ip_processing.py` (Main Script)

Direct execution (runs in foreground):

```bash
cd /home/tuancuong112504/prj5-gcp/source
source .venv/bin/activate
python run_ip_processing.py
```

**Output:**
- Real-time progress with timestamps
- Progress every 1000 IPs
- Final statistics

### `run_with_nohup.sh` (Background Execution)

Runs the processor in background with nohup:

```bash
bash run_with_nohup.sh
```

**Benefits:**
- Process continues even if you disconnect SSH
- Real-time logging to `ip_processing.log`
- Shows process PID for monitoring

### `monitor_progress.sh` (Real-Time Monitoring)

Follow the log file live:

```bash
bash monitor_progress.sh
```

Press `Ctrl+C` to stop monitoring (process keeps running).

---

## Processing Stages & Timeline

### Stage 1: MongoDB Index Creation
- **Duration:** 15-30 minutes
- **What:** Building index on 'ip' field across 41.4M documents
- **Log Output:** `Creating index on 'ip' field...`

### Stage 2: Extract Unique IPs
- **Duration:** 30 minutes - 2+ hours
- **What:** Scanning 41.4M documents, extracting unique IP addresses
- **Log Output:** Progress every 100,000 IPs
- **Example:** `Progress: 100,000 unique IPs found...`

### Stage 3: IP Lookup & Storage
- **Duration:** Variable (5-10 seconds per 1000 IPs)
- **What:** Looking up each unique IP in IP2Location database, storing results
- **Log Output:** Progress every 1000 IPs
- **Example:** `Progress: 1,000/50,000 (2.0%) | Successful: 950 | Failed: 50`

### Stage 4: Write CSV
- **Duration:** 5-10 minutes
- **What:** Writing all processed IPs to CSV file
- **Log Output:** `CSV file written: /path/to/ip_locations.csv`

---

## Log Output Examples

### Successful Start

```
[2026-04-21 14:30:45] ================================================================================
[2026-04-21 14:30:45] TASK 5: IP Location Processing - Large Dataset Edition
[2026-04-21 14:30:45] ================================================================================
[2026-04-21 14:30:45] 
[2026-04-21 14:30:45] ⚠️  DATASET SIZE: 41.4 million documents (34 GB)
[2026-04-21 14:30:45] ⏱️  EXPECTED DURATION: 2-6 hours depending on system resources
[2026-04-21 14:30:45] 
[2026-04-21 14:30:48] [1] Connecting to MongoDB...
[2026-04-21 14:30:49] ✓ Connected to MongoDB: mongodb://localhost:27017
[2026-04-21 14:30:50] [2] Loading IP2Location database...
[2026-04-21 14:30:50] ✓ IP2Location database loaded: /home/tuancuong112504/prj5-gcp/monggodb-data/IP-COUNTRY-REGION-CITY.BIN
```

### During Processing

```
[2026-04-21 15:45:30]   Progress: 1,000/50,000 (2.0%) | Successful: 950 | Failed: 50
[2026-04-21 15:46:15]   Progress: 2,000/50,000 (4.0%) | Successful: 1,900 | Failed: 100
[2026-04-21 15:47:00]   Progress: 3,000/50,000 (6.0%) | Successful: 2,850 | Failed: 150
```

### Completion

```
[2026-04-21 18:45:30] ================================================================================
[2026-04-21 18:45:30] ✅ PROCESSING COMPLETE
[2026-04-21 18:45:30] ================================================================================
[2026-04-21 18:45:30] Status: completed
[2026-04-21 18:45:30] Total IPs processed: 50,000
[2026-04-21 18:45:30]   ✓ Successful: 49,750
[2026-04-21 18:45:30]   ✗ Failed: 250
[2026-04-21 18:45:30] 
[2026-04-21 18:45:30] Output:
[2026-04-21 18:45:30]   MongoDB Collection: countly.ip_locations
[2026-04-21 18:45:30]   CSV File: /home/tuancuong112504/prj5-gcp/output/ip_locations.csv
```

---

## Monitoring & Management

### Check Process Status

```bash
# Get process ID and status
ps -p <PID>

# Or from the earlier nohup output
ps aux | grep "run_ip_processing.py"
```

### View Last 100 Lines of Log

```bash
tail -100 ip_processing.log
```

### View Last 50 Lines and Follow

```bash
tail -f -n 50 ip_processing.log
```

### Count Progress (Unique IPs processed so far)

```bash
grep "Progress:" ip_processing.log | tail -5
```

### Kill Process (if needed)

```bash
# Replace <PID> with the actual process ID
kill <PID>

# Force kill if needed
kill -9 <PID>
```

---

## Output Locations

### MongoDB Collection

**Database:** `countly`
**Collection:** `ip_locations`

Fields stored:
- `ip` (unique index)
- `country_code`, `country_name`
- `region_name`, `city_name`
- `latitude`, `longitude`
- `zip_code`, `time_zone`
- `isp`, `domain`, `net_speed`
- `elevation`, `usage_type`
- `processed_at` (timestamp)

### CSV File

**Location:** `/home/tuancuong112504/prj5-gcp/output/ip_locations.csv`

Contains all fields in CSV format, one IP per row.

---

## Troubleshooting

### Log File Not Updating

1. Check if process is still running:
   ```bash
   ps aux | grep "run_ip_processing.py"
   ```

2. The process might be in a slow stage (e.g., index creation). Wait a bit longer.

3. Check for errors:
   ```bash
   tail -50 ip_processing.log | grep -i "error"
   ```

### MongoDB Connection Failed

Verify MongoDB is running:

```bash
mongo --eval "db.adminCommand('ping')"
```

### Out of Memory

The process may be consuming too much RAM. You can:

1. Reduce batch size by modifying `run_ip_processing.py`:
   ```python
   chunk_size: int = 500,  # Instead of 1000
   ```

2. Restart and try again

### Process Takes Too Long

- This is normal for 41.4M documents
- Check current progress with `tail -f ip_processing.log`
- Index creation can take 15-60 minutes alone
- Patient waiting is required

---

## Performance Optimization

If processing is very slow:

1. **Increase system resources:**
   - More CPU cores
   - More RAM
   - Faster disk (SSD)

2. **MongoDB optimization:**
   - Ensure MongoDB has adequate memory
   - Check MongoDB logs: `/var/log/mongodb/mongod.log`
   - Verify no other heavy queries running

3. **Python optimization:**
   - Increase chunk_size in code for faster batching
   - Adjust batch_size in MongoDB aggregation

---

## Success Checklist

- [ ] Start process with `bash run_with_nohup.sh`
- [ ] Monitor with `bash monitor_progress.sh` or `tail -f ip_processing.log`
- [ ] Watch for progress updates every 1000 IPs
- [ ] Wait for "✅ PROCESSING COMPLETE" message
- [ ] Verify output collection in MongoDB: `countly.ip_locations`
- [ ] Verify CSV file: `output/ip_locations.csv`
- [ ] Check statistics (total, successful, failed)

---

## Next Steps After Completion

1. **Verify Data:**
   ```python
   from pymongo import MongoClient
   client = MongoClient("mongodb://localhost:27017")
   db = client["countly"]
   print(f"Total IPs in collection: {db.ip_locations.count_documents({})}")
   print(f"Sample IP: {db.ip_locations.find_one()}")
   ```

2. **Analyze Results:**
   - Import CSV into analysis tool
   - Query MongoDB for geographic statistics
   - Generate reports

3. **Next Tasks:**
   - Tasks 6, 7, etc.

---

**Good luck with your IP location processing! 🚀**
