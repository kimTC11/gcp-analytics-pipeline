#!/usr/bin/env python3
"""
Data Quality Verification Script
Comprehensive verification of processed data integrity
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

def print_header(title):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def log_check(name, status, details=""):
    """Log a verification check result"""
    symbol = "✓" if status else "✗"
    color_code = "\033[92m" if status else "\033[91m"  # Green or Red
    reset_code = "\033[0m"
    
    print(f"{color_code}{symbol}{reset_code} {name}")
    if details:
        print(f"  └─ {details}")

def verify_mongodb():
    """Verify MongoDB data and collections"""
    print_header("MongoDB Data Verification")
    
    all_passed = True
    
    try:
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        db = client['countly']
        
        # Connection test
        client.admin.command('ping')
        log_check("MongoDB connection", True)
        
    except ServerSelectionTimeoutError:
        log_check("MongoDB connection", False, "Could not connect to MongoDB")
        return False
    except Exception as e:
        log_check("MongoDB connection", False, str(e))
        return False
    
    try:
        # Check ip_locations collection
        try:
            ip_count = db.ip_locations.count_documents({})
            ip_passed = ip_count >= 3000000
            log_check(
                "ip_locations collection",
                ip_passed,
                f"{ip_count:,} documents (expected ~3.2M)"
            )
            if not ip_passed:
                all_passed = False
            
            # Check IP uniqueness
            if ip_count > 0:
                duplicate_check = db.ip_locations.aggregate([
                    {"$group": {"_id": "$ip", "count": {"$sum": 1}}},
                    {"$match": {"count": {"$gt": 1}}}
                ])
                duplicates = list(duplicate_check)
                log_check(
                    "IP uniqueness",
                    len(duplicates) == 0,
                    f"{len(duplicates)} duplicate IPs found" if duplicates else "No duplicates"
                )
                if duplicates:
                    all_passed = False
            
            # Check data completeness
            if ip_count > 0:
                completeness = db.ip_locations.aggregate([
                    {"$group": {
                        "_id": None,
                        "total": {"$sum": 1},
                        "with_country": {"$sum": {"$cond": [{"$ne": ["$country", None]}, 1, 0]}},
                        "with_city": {"$sum": {"$cond": [{"$ne": ["$city", None]}, 1, 0]}},
                        "with_coords": {"$sum": {"$cond": [{"$ne": ["$latitude", None]}, 1, 0]}}
                    }}
                ])
                stats = list(completeness)[0] if completeness else {}
                
                if stats:
                    country_pct = (stats['with_country'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    city_pct = (stats['with_city'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    coords_pct = (stats['with_coords'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    
                    log_check(
                        "IP data completeness",
                        country_pct >= 95 and city_pct >= 90,
                        f"Country: {country_pct:.1f}%, City: {city_pct:.1f}%, Coords: {coords_pct:.1f}%"
                    )
                    if country_pct < 95 or city_pct < 90:
                        all_passed = False
                
                # Check index
                indexes = db.ip_locations.list_indexes()
                has_ip_index = any(idx['name'] == 'ip_1' for idx in indexes)
                log_check(
                    "IP index created",
                    has_ip_index,
                    "Index on 'ip' field" if has_ip_index else "No index found"
                )
        
        except Exception as e:
            log_check("ip_locations collection", False, str(e))
            all_passed = False
        
        try:
            # Check products collection
            product_count = db.products.count_documents({})
            product_passed = product_count >= 15000
            log_check(
                "products collection",
                product_passed,
                f"{product_count:,} documents (expected ~19K)"
            )
            if not product_passed:
                all_passed = False
            
            # Check product uniqueness
            if product_count > 0:
                product_duplicates = db.products.aggregate([
                    {"$group": {"_id": "$product_id", "count": {"$sum": 1}}},
                    {"$match": {"count": {"$gt": 1}}}
                ])
                dups = list(product_duplicates)
                log_check(
                    "Product ID uniqueness",
                    len(dups) == 0,
                    f"{len(dups)} duplicates" if dups else "No duplicates"
                )
                if dups:
                    all_passed = False
            
            # Check product data quality
            if product_count > 0:
                product_stats = db.products.aggregate([
                    {"$group": {
                        "_id": None,
                        "total": {"$sum": 1},
                        "with_name": {"$sum": {"$cond": [{"$ne": ["$product_name", None]}, 1, 0]}},
                        "with_urls": {"$sum": {"$cond": [{"$gt": [{"$size": "$urls"}, 0]}, 1, 0]}},
                        "with_events": {"$sum": {"$cond": [{"$gt": [{"$size": "$event_types"}, 0]}, 1, 0]}}
                    }}
                ])
                p_stats = list(product_stats)[0] if product_stats else {}
                
                if p_stats:
                    name_pct = (p_stats['with_name'] / p_stats['total'] * 100) if p_stats['total'] > 0 else 0
                    url_pct = (p_stats['with_urls'] / p_stats['total'] * 100) if p_stats['total'] > 0 else 0
                    event_pct = (p_stats['with_events'] / p_stats['total'] * 100) if p_stats['total'] > 0 else 0
                    
                    log_check(
                        "Product data completeness",
                        name_pct >= 95 and url_pct >= 95,
                        f"Names: {name_pct:.1f}%, URLs: {url_pct:.1f}%, Events: {event_pct:.1f}%"
                    )
                    if name_pct < 95 or url_pct < 95:
                        all_passed = False
        
        except Exception as e:
            log_check("products collection", False, str(e))
            all_passed = False
        
        client.close()
        return all_passed
    
    except Exception as e:
        log_check("MongoDB verification", False, str(e))
        return False

def verify_output_files():
    """Verify output files exist and contain valid data"""
    print_header("Output Files Verification")
    
    all_passed = True
    base_path = Path('/home/tuancuong112504/prj5-gcp/output')
    
    # Check IP locations CSV
    try:
        ip_csv = base_path / 'ip_locations.csv'
        if ip_csv.exists():
            size_mb = ip_csv.stat().st_size / (1024 * 1024)
            with open(ip_csv, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            csv_passed = len(rows) >= 3000000 and size_mb >= 700
            log_check(
                "ip_locations.csv",
                csv_passed,
                f"{len(rows):,} rows, {size_mb:.0f}MB (expected 3.2M+ rows, 800MB+)"
            )
            
            if csv_passed and rows:
                # Check columns
                expected_cols = {'ip', 'country', 'city', 'latitude', 'longitude'}
                has_cols = expected_cols.issubset(set(rows[0].keys()))
                log_check(
                    "CSV columns",
                    has_cols,
                    f"Columns: {', '.join(rows[0].keys())}"
                )
                if not has_cols:
                    all_passed = False
            elif not csv_passed:
                all_passed = False
        else:
            log_check("ip_locations.csv", False, "File not found")
            all_passed = False
    
    except Exception as e:
        log_check("ip_locations.csv", False, str(e))
        all_passed = False
    
    # Check products JSON
    try:
        products_json = base_path / 'products.json'
        if products_json.exists():
            with open(products_json, 'r') as f:
                products = json.load(f)
            
            json_passed = len(products) >= 15000
            log_check(
                "products.json",
                json_passed,
                f"{len(products):,} products (expected 19K+)"
            )
            
            if json_passed and products:
                # Check data structure
                with_names = sum(1 for p in products if p.get('product_name'))
                with_ids = sum(1 for p in products if p.get('product_id'))
                
                name_pct = (with_names / len(products)) * 100
                log_check(
                    "Product names extracted",
                    name_pct >= 95,
                    f"{with_names}/{len(products)} ({name_pct:.1f}%)"
                )
                if name_pct < 95:
                    all_passed = False
            elif not json_passed:
                all_passed = False
        else:
            log_check("products.json", False, "File not found")
            all_passed = False
    
    except Exception as e:
        log_check("products.json", False, str(e))
        all_passed = False
    
    # Check products CSV
    try:
        products_csv = base_path / 'products.csv'
        if products_csv.exists():
            with open(products_csv, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            csv_passed = len(rows) >= 15000
            log_check(
                "products.csv",
                csv_passed,
                f"{len(rows):,} rows (expected 19K+)"
            )
            if not csv_passed:
                all_passed = False
        else:
            log_check("products.csv", False, "File not found")
            all_passed = False
    
    except Exception as e:
        log_check("products.csv", False, str(e))
        all_passed = False
    
    return all_passed

def verify_log_files():
    """Verify log files exist and contain completion markers"""
    print_header("Log Files Verification")
    
    all_passed = True
    log_dir = Path('/home/tuancuong112504/prj5-gcp/log')
    
    # Check IP processing log
    try:
        ip_log = log_dir / 'ip_processing.log'
        if ip_log.exists():
            content = ip_log.read_text()
            
            has_complete = '✅ PROCESSING COMPLETE' in content
            log_check(
                "ip_processing.log",
                has_complete,
                "Execution completed successfully" if has_complete else "Incomplete execution"
            )
            
            if not has_complete:
                all_passed = False
                # Check for errors
                if 'error' in content.lower() or 'failed' in content.lower():
                    log_check("Error detection", False, "Errors found in log")
        else:
            log_check("ip_processing.log", False, "File not found")
            all_passed = False
    
    except Exception as e:
        log_check("ip_processing.log", False, str(e))
        all_passed = False
    
    # Check product processing log
    try:
        product_log = log_dir / 'product_collection.log'
        if product_log.exists():
            content = product_log.read_text()
            
            has_complete = '✅ PROCESSING COMPLETE' in content
            log_check(
                "product_collection.log",
                has_complete,
                "Execution completed successfully" if has_complete else "Still running or incomplete"
            )
            
            if not has_complete and 'Processing Duration' not in content:
                all_passed = False
        else:
            log_check("product_collection.log", False, "File not found (may be still running)")
    
    except Exception as e:
        log_check("product_collection.log", False, str(e))
        all_passed = False
    
    return all_passed

def generate_summary(mongodb_ok, files_ok, logs_ok):
    """Generate final summary report"""
    print_header("Verification Summary")
    
    all_passed = mongodb_ok and files_ok and logs_ok
    
    status = "✓ ALL CHECKS PASSED" if all_passed else "✗ SOME CHECKS FAILED"
    status_color = "\033[92m" if all_passed else "\033[91m"
    reset = "\033[0m"
    
    print(f"{status_color}{status}{reset}")
    print(f"\nComponent Status:")
    print(f"  {'✓' if mongodb_ok else '✗'} MongoDB data integrity")
    print(f"  {'✓' if files_ok else '✗'} Output files validity")
    print(f"  {'✓' if logs_ok else '✗'} Execution logs")
    
    if all_passed:
        print(f"\n✓ Data processing pipeline is complete and valid!")
        print(f"✓ Ready for analysis and downstream processing")
    else:
        print(f"\n✗ Please review failed checks above")
        print(f"✗ Check log files for error details")
    
    print(f"\nVerification timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def main():
    """Main verification routine"""
    print("\n" + "="*70)
    print("  DATA QUALITY VERIFICATION REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Run all verifications
    mongodb_ok = verify_mongodb()
    files_ok = verify_output_files()
    logs_ok = verify_log_files()
    
    # Generate summary
    generate_summary(mongodb_ok, files_ok, logs_ok)
    
    # Return appropriate exit code
    return 0 if (mongodb_ok and files_ok and logs_ok) else 1

if __name__ == '__main__':
    sys.exit(main())
