#!/usr/bin/env python
"""
Task 5: IP Location Processing
Processes unique IPs from countly.summary collection and enriches with location data.
Stores results in MongoDB collection and CSV file.

⚠️  NOTE: For large datasets (millions of documents), this may take significant time:
    - Extracting unique IPs: ~30 min - 2+ hours (depending on dataset size and disk speed)
    - IP lookup: ~5-10 seconds per 1000 IPs
    - Total time for 41.4M documents: Potentially several hours
    
Progress is reported every 1000 IPs processed.

Usage with nohup (runs in background):
    nohup python run_ip_processing.py > ip_processing.log 2>&1 &
    
Monitor progress:
    tail -f ip_processing.log
"""

import sys
from pathlib import Path

# Add src directory to path so we can import from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ip_location_processor import IPLocationProcessor
from datetime import datetime
import time


def log_print(msg: str):
    """Print message with timestamp and flush immediately for real-time output."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()


def main():
    """Main execution for Task 5: IP Location Processing."""
    
    # Configuration
    MONGO_URI = "mongodb://localhost:27017"
    DB_NAME = "countly"
    SOURCE_COLLECTION = "summary"
    OUTPUT_COLLECTION = "ip_locations"
    OUTPUT_CSV = "/home/tuancuong112504/prj5-gcp/log/ip_locations.csv"
    
    log_print("=" * 80)
    log_print("TASK 5: IP Location Processing - Large Dataset Edition")
    log_print("=" * 80)
    log_print("")
    log_print("⚠️  DATASET SIZE: 41.4 million documents (34 GB)")
    log_print("⏱️  EXPECTED DURATION: 2-6 hours depending on system resources")
    log_print("")
    log_print("Configuration:")
    log_print(f"  MongoDB URI: {MONGO_URI}")
    log_print(f"  Database: {DB_NAME}")
    log_print(f"  Source Collection: {SOURCE_COLLECTION}")
    log_print(f"  Output Collection: {OUTPUT_COLLECTION}")
    log_print(f"  Output CSV: {OUTPUT_CSV}")
    log_print("")
    
    start_time = time.time()
    
    # Initialize processor
    processor = IPLocationProcessor(
        mongo_uri=MONGO_URI,
        db_name=DB_NAME,
    )
    
    try:
        # Step 1: Connect to MongoDB
        log_print("[1] Connecting to MongoDB...")
        if not processor.connect_mongodb():
            log_print("❌ Failed to connect to MongoDB. Exiting.")
            return False
        
        # Step 2: Load IP2Location database
        log_print("\n[2] Loading IP2Location database...")
        if not processor.load_ip2location():
            log_print("❌ Failed to load IP2Location database. Exiting.")
            return False
        
        # Step 3: Process IP locations
        log_print(f"\n[3] Processing unique IPs from '{SOURCE_COLLECTION}' collection...")
        log_print("    This step will take the longest - showing progress every 1000 IPs...\n")
        
        step3_start = time.time()
        stats = processor.process_ip_locations(
            source_collection=SOURCE_COLLECTION,
            output_collection=OUTPUT_COLLECTION,
            output_csv=OUTPUT_CSV,
        )
        step3_duration = time.time() - step3_start
        
        # Display final results
        total_duration = time.time() - start_time
        
        log_print("\n" + "=" * 80)
        log_print("✅ PROCESSING COMPLETE")
        log_print("=" * 80)
        log_print(f"Status: {stats['status']}")
        log_print(f"Total IPs processed: {stats['total_processed']:,}")
        log_print(f"  ✓ Successful: {stats['successful']:,}")
        log_print(f"  ✗ Failed: {stats['failed']:,}")
        log_print(f"\nOutput:")
        log_print(f"  MongoDB Collection: {stats['output_collection']}")
        if stats['output_csv']:
            log_print(f"  CSV File: {stats['output_csv']}")
        log_print(f"\nProcessed at: {stats['timestamp']}")
        log_print(f"\n⏱️  Timing:")
        log_print(f"  Step 3 (IP Processing): {step3_duration/60:.1f} minutes ({step3_duration/3600:.2f} hours)")
        log_print(f"  Total Duration: {total_duration/60:.1f} minutes ({total_duration/3600:.2f} hours)")
        log_print("=" * 80)
        
        return True
    
    except KeyboardInterrupt:
        log_print("\n\n⚠️  Process interrupted by user (Ctrl+C)")
        log_print("Cleaning up and closing connections...")
        return False
    except Exception as e:
        log_print(f"\n❌ Unexpected error: {e}")
        import traceback
        log_print(traceback.format_exc())
        return False
    
    finally:
        processor.close()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
