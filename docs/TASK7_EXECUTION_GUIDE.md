# Task 7: React Data Extraction (Web Crawling) - Execution Guide

## Overview

Extracts detailed product information from Glamira product pages using browser automation (Playwright). Processes all 19,417 products with retry logic and fallback URLs.

**Duration:** ~25 minutes
**Success Rate:** 97.7% (18,969/19,417 products)
**Output Size:** 5.8 MB across 195 success files + 86 error logs

---

## What It Does

1. **Fetches Product Pages** - Uses Playwright to load each product's page with 2.5s wait
2. **Extracts React Data** - Parses the `react_data` JSON variable from page HTML
3. **Retry Logic** - Up to 3 attempts per URL before falling back
4. **Fallback URLs** - Retries with alternate product page format if original fails
5. **Metadata Extraction** - Captures price currency and discount values
6. **Batch Processing** - Processes 100 items per batch with 8 concurrent workers

---

## Quick Start (Run in Background)

### 1️⃣  Start Crawling with nohup

```bash
cd /home/tuancuong112504/prj5-gcp
nohup python -u src/runners/run_full_crawl.py > logs/crawl.log 2>&1 &
```

Or use the provided script:

```bash
cd /home/tuancuong112504/prj5-gcp
bash src/scripts/run_with_nohup.sh
```

### 2️⃣  Monitor Progress in Real-Time

```bash
tail -f logs/crawl.log
```

Watch for progress updates showing:
- Current product count `[N/19,417]`
- Percentage complete
- Success/fail counts
- ETA to completion

---

## Key Configuration

Located in [src/runners/run_full_crawl.py](../../src/runners/run_full_crawl.py#L20-L30):

```python
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
TIMEOUT_MS = 20000          # Page load timeout (20 seconds)
WAIT_MS = 2500              # Wait after load (2.5 seconds)
MAX_CONCURRENT = 8          # Parallel workers
CHUNK_SIZE = 100            # Items per batch
RETRIES = 3                 # Attempts per URL
```

---

## Input & Output

### Input
- **Source:** [output/products.csv](../../output/products.csv)
- **Records:** 19,417 products with ID and URL

### Output

**Success Files:** `output_crawl/react_batch_part_*.csv` (195 files)
- Contains 18,969 successfully scraped products
- Columns: product_id, url, success, fall_back, crawled_at, name, sku, price, product_type, gender, type_id, collection, priceCurrency, discount-value

**Error Files:** `output_crawl/react_batch_error_part_*.csv` (86 files)
- Contains 448 failed products
- Columns: product_id, url, success, fall_back, error, crawled_at

---

## Results Summary

```
✅ Done: success=18,969 fail=448
Success Rate: 97.7%
Duration: ~25 minutes
Output Size: 5.8 MB
Success Files: 195
Error Files: 86
```

### Success Breakdown
- **Original URL Success:** ~95% of products on first try
- **Fallback URL Success:** Recovers most remaining failures
- **Final Failures:** 448 products (2.3%) - mostly obsolete or blocked pages

---

## Data Validation

### Check Results

```bash
# Count success records
python3 << 'EOF'
import pandas as pd
import glob
files = glob.glob("output_crawl/react_batch_part_*.csv")
total = sum(len(pd.read_csv(f)) for f in files)
print(f"Total successful records: {total:,}")
EOF
```

### Verify Data Quality

```bash
# Check for missing fields
python3 << 'EOF'
import pandas as pd
import glob

files = glob.glob("output_crawl/react_batch_part_*.csv")
dfs = [pd.read_csv(f) for f in files]
combined = pd.concat(dfs, ignore_index=True)

print(f"Total records: {len(combined):,}")
print(f"Has name: {combined['name'].notna().sum():,}")
print(f"Has price: {combined['price'].notna().sum():,}")
print(f"Fallback used: {combined['fall_back'].sum():,}")
EOF
```

---

## Troubleshooting

### Script Fails to Start
- Check Playwright is installed: `pip list | grep playwright`
- Install if missing: `pip install playwright`

### Crawler Getting Blocked
- Glamira may rate-limit. Check `error` field in error files
- Consider increasing `WAIT_MS` or reducing `MAX_CONCURRENT`

### No Progress After Starting
- Check logs: `tail -f logs/crawl.log`
- Process may be initializing browsers (takes 10-30 seconds)
- Allow 1-2 minutes before concluding it's stuck

### Specific Product Fails Repeatedly
- Check error CSV files for that product_id
- Error field shows: timeout, network error, or parse failure
- May be product page is discontinued or blocked

---

## Next Steps

1. **Consolidate Results** - Merge 195 success CSV files into single file
2. **Analyze Failures** - Review 448 failed products in error files
3. **Data Quality Report** - Run `data_quality_report.py` to validate
4. **Export Results** - Convert to final output format (JSON/Parquet)

---

## Technical Details

### Retry Strategy
1. **Original URL** (3 attempts)
   - Initial page load
   - Waits 1-3 seconds between retries
2. **Fallback URL** (3 attempts)
   - Alternative catalog view format
   - Same retry logic as original

### Concurrent Processing
- 8 parallel Playwright instances
- Each processes 100-item chunk before saving
- Batch output written immediately (fault-tolerant)

### Browser Automation
- **Engine:** Chromium (Playwright)
- **Mode:** Headless (no GUI)
- **JavaScript:** Executes to populate react_data
- **Memory:** ~200-400 MB for 8 browsers

---

## Performance Notes

- **Throughput:** ~12-15 products/second
- **Memory Usage:** ~500 MB peak
- **Network:** Depends on Glamira server capacity
- **Total Duration:** 20-30 minutes for full 19,417 products

For sustained crawling, monitor system resources:
```bash
watch -n 5 'ps aux | grep playwright'
```
