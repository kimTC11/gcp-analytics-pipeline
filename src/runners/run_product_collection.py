#!/usr/bin/env python
"""
Task 6: Product Information Collection Runner
Processes product data with real-time logging
"""

import sys
from pathlib import Path

# Add src directory to path so we can import from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.product_collector import ProductCollector
from datetime import datetime
import time


def log_print(msg: str):
    """Print message with timestamp and flush immediately for real-time output."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()


def main():
    """Main execution for Task 6: Product Information Collection."""
    
    # Configuration
    MONGO_URI = "mongodb://localhost:27017"
    DB_NAME = "countly"
    SOURCE_COLLECTION = "summary"
    OUTPUT_JSON = "/home/tuancuong112504/prj5-gcp/output/products.json"
    OUTPUT_CSV = "/home/tuancuong112504/prj5-gcp/output/products.csv"
    
    log_print("=" * 80)
    log_print("TASK 6: Product Information Collection")
    log_print("=" * 80)
    log_print("")
    log_print("⚠️  This task extracts product data from 41.4M event records")
    log_print("⏱️  EXPECTED DURATION: 1-2 hours depending on system resources")
    log_print("")
    log_print("Configuration:")
    log_print(f"  MongoDB URI: {MONGO_URI}")
    log_print(f"  Database: {DB_NAME}")
    log_print(f"  Source Collection: {SOURCE_COLLECTION}")
    log_print(f"  Output JSON: {OUTPUT_JSON}")
    log_print(f"  Output CSV: {OUTPUT_CSV}")
    log_print("")
    
    start_time = time.time()
    
    # Initialize collector
    collector = ProductCollector(
        mongo_uri=MONGO_URI,
        db_name=DB_NAME,
        source_collection=SOURCE_COLLECTION,
    )
    
    try:
        # Step 1: Connect to MongoDB
        log_print("[1] Connecting to MongoDB...")
        if not collector.connect_mongodb():
            log_print("❌ Failed to connect to MongoDB. Exiting.")
            return False
        
        # Step 2: Process products
        log_print("\n[2] Processing product information...")
        log_print("    Filtering events and extracting URLs...")
        log_print("    Extracting product names from URLs...")
        log_print("")
        
        step2_start = time.time()
        stats = collector.process_products(
            output_json=OUTPUT_JSON,
            output_csv=OUTPUT_CSV,
        )
        step2_duration = time.time() - step2_start
        
        # Display final results
        total_duration = time.time() - start_time
        
        log_print("")
        log_print("=" * 80)
        log_print("✅ PROCESSING COMPLETE")
        log_print("=" * 80)
        log_print(f"Status: {stats['status']}")
        log_print(f"Total products extracted: {stats['total_products']:,}")
        log_print(f"  ✓ With product name: {stats['with_product_name']:,}")
        log_print(f"  ✗ Without product name: {stats['without_product_name']:,}")
        log_print(f"\nOutput files:")
        if stats['output_json']:
            log_print(f"  JSON: {stats['output_json']}")
        if stats['output_csv']:
            log_print(f"  CSV: {stats['output_csv']}")
        log_print(f"\nProcessed at: {stats['timestamp']}")
        log_print(f"\n⏱️  Timing:")
        log_print(f"  Processing Duration: {step2_duration/60:.1f} minutes ({step2_duration/3600:.2f} hours)")
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
        collector.close()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
