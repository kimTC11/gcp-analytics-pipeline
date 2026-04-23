#!/usr/bin/env python3
"""
Data Quality Verification & Reporting
Comprehensive validation of all processed data outputs
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


class DataQualityReport:
    """Comprehensive data quality verification and reporting"""
    
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017"):
        self.mongo_uri = mongo_uri
        self.client = None
        self.db = None
        self.results = {}
        self.issues = []
        self.warnings = []
    
    def _log(self, msg: str, level: str = "INFO") -> None:
        """Print formatted log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        symbol_map = {"✓": "✓", "✗": "✗", "⚠": "⚠", "INFO": "ℹ", "SUCCESS": "✓", "ERROR": "✗", "WARNING": "⚠"}
        symbol = symbol_map.get(level, "ℹ")
        print(f"[{timestamp}] {symbol} {msg}")
        sys.stdout.flush()
    
    def connect_mongodb(self) -> bool:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client['countly']
            self.client.admin.command('ping')
            self._log("MongoDB connection successful", "SUCCESS")
            return True
        except ServerSelectionTimeoutError:
            self._log("MongoDB connection failed - server timeout", "ERROR")
            return False
        except Exception as e:
            self._log(f"MongoDB connection error: {e}", "ERROR")
            return False
    
    def verify_mongodb_data(self) -> Dict[str, Any]:
        """Verify MongoDB collections and data integrity"""
        self._log("\n=== MONGODB DATA VERIFICATION ===\n", "INFO")
        
        if not self.client:
            self._log("MongoDB not connected, skipping verification", "WARNING")
            return {}
        
        checks = {}
        
        try:
            # Check summary collection (source data)
            summary = self.db['summary']
            self._log(f"Checking summary collection...", "INFO")
            summary_exists = summary.count_documents({}, limit=1) > 0
            if summary_exists:
                self._log(f"✓ Summary collection exists and has data", "SUCCESS")
                checks['summary_exists'] = True
            else:
                self._log(f"⚠ Summary collection may be empty", "WARNING")
                checks['summary_exists'] = False
            
            # Check IP locations
            ip_locs = self.db['ip_locations']
            self._log(f"Checking IP locations collection...", "INFO")
            ip_sample = ip_locs.find_one()
            if ip_sample:
                self._log(f"✓ IP locations collection has data", "SUCCESS")
                checks['ip_locations_exists'] = True
            else:
                self._log(f"⚠ IP locations collection may be empty", "WARNING")
                checks['ip_locations_exists'] = False
            
            # Sample data check
            sample_doc = ip_locs.find_one()
            if sample_doc:
                checks['ip_sample'] = {
                    'has_ip': 'ip' in sample_doc,
                    'has_country': 'country' in sample_doc,
                    'has_region': 'region' in sample_doc,
                    'has_city': 'city' in sample_doc,
                }
                if all(checks['ip_sample'].values()):
                    self._log("✓ IP location document structure validated", "SUCCESS")
                else:
                    missing = [k for k, v in checks['ip_sample'].items() if not v]
                    self._log(f"⚠ Missing fields in IP doc: {missing}", "WARNING")
        
        except Exception as e:
            self._log(f"Error verifying MongoDB: {e}", "ERROR")
            self.issues.append(str(e))
        
        self.results['mongodb'] = checks
        return checks
    
    def verify_output_files(self) -> Dict[str, Any]:
        """Verify output CSV and JSON files"""
        self._log("\n=== OUTPUT FILES VERIFICATION ===\n", "INFO")
        
        checks = {}
        output_dir = Path(__file__).parent.parent.parent / "output"
        
        # Check products CSV
        products_csv = output_dir / "products.csv"
        if products_csv.exists():
            with open(products_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            checks['products_csv'] = {
                'exists': True,
                'rows': len(rows),
                'columns': list(reader.fieldnames) if reader.fieldnames else []
            }
            
            self._log(f"products.csv: {len(rows):,} records", "INFO")
            
            # Validate structure
            required_cols = {'product_id', 'product_name', 'url', 'event_type', 'timestamp'}
            actual_cols = set(checks['products_csv']['columns'])
            
            if required_cols.issubset(actual_cols):
                self._log("✓ Products CSV structure validated", "SUCCESS")
            else:
                missing = required_cols - actual_cols
                self._log(f"⚠ Missing columns in products.csv: {missing}", "WARNING")
                self.warnings.append(f"Missing CSV columns: {missing}")
            
            # Check data quality
            if rows:
                sample = rows[0]
                valid_ids = sum(1 for r in rows if r.get('product_id', '').strip())
                valid_names = sum(1 for r in rows if r.get('product_name', '').strip())
                
                checks['products_csv_quality'] = {
                    'rows_with_id': valid_ids,
                    'rows_with_name': valid_names,
                    'quality_score': f"{(valid_names/len(rows)*100):.1f}%" if rows else "0%"
                }
                
                self._log(f"  Product IDs present: {valid_ids}/{len(rows)}", "INFO")
                self._log(f"  Product names present: {valid_names}/{len(rows)}", "INFO")
        else:
            self._log("products.csv not found", "ERROR")
            self.issues.append("products.csv missing")
        
        # Check products JSON
        products_json = output_dir / "products.json"
        if products_json.exists():
            with open(products_json, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            checks['products_json'] = {
                'exists': True,
                'unique_products': len(json_data),
            }
            
            self._log(f"products.json: {len(json_data):,} unique products", "INFO")
            
            # Validate structure
            if json_data:
                first_key = list(json_data.keys())[0]
                first_doc = json_data[first_key]
                required_fields = {'product_id', 'product_name', 'url', 'event_type', 'timestamp'}
                actual_fields = set(first_doc.keys())
                
                if required_fields.issubset(actual_fields):
                    self._log("✓ Products JSON structure validated", "SUCCESS")
                else:
                    missing = required_fields - actual_fields
                    self._log(f"⚠ Missing fields in products.json: {missing}", "WARNING")
        else:
            self._log("products.json not found", "ERROR")
            self.issues.append("products.json missing")
        
        # Check IP locations CSV
        ip_csv = Path(__file__).parent.parent.parent / "log" / "ip_locations.csv"
        if ip_csv.exists():
            with open(ip_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                ip_rows = list(reader)
            
            checks['ip_csv'] = {
                'exists': True,
                'rows': len(ip_rows),
            }
            
            self._log(f"ip_locations.csv: {len(ip_rows):,} records", "INFO")
            
            if ip_rows:
                sample = ip_rows[0]
                has_ip = 'ip' in sample
                has_country = 'country' in sample
                
                if has_ip and has_country:
                    self._log("✓ IP CSV structure validated", "SUCCESS")
                else:
                    self._log("⚠ IP CSV missing expected columns", "WARNING")
        else:
            self._log("ip_locations.csv not found (may be expected)", "WARNING")
        
        self.results['output_files'] = checks
        return checks
    
    def verify_data_consistency(self) -> Dict[str, Any]:
        """Verify consistency between sources"""
        self._log("\n=== DATA CONSISTENCY CHECKS ===\n", "INFO")
        
        checks = {}
        output_dir = Path(__file__).parent.parent.parent / "output"
        products_csv = output_dir / "products.csv"
        products_json = output_dir / "products.json"
        
        try:
            if products_csv.exists() and products_json.exists():
                # Load both formats
                csv_ids = set()
                with open(products_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    csv_ids = {row['product_id'] for row in reader if row.get('product_id')}
                
                with open(products_json, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    json_ids = set(json_data.keys())
                
                checks['product_id_consistency'] = {
                    'csv_count': len(csv_ids),
                    'json_count': len(json_ids),
                    'matching': len(csv_ids & json_ids),
                }
                
                self._log(f"CSV product IDs: {len(csv_ids)}", "INFO")
                self._log(f"JSON product IDs: {len(json_ids)}", "INFO")
                self._log(f"Matching IDs: {len(csv_ids & json_ids)}", "INFO")
                
                if csv_ids == json_ids:
                    self._log("✓ CSV and JSON contain identical product IDs", "SUCCESS")
                else:
                    only_csv = csv_ids - json_ids
                    only_json = json_ids - csv_ids
                    if only_csv:
                        self._log(f"⚠ {len(only_csv)} IDs in CSV but not JSON", "WARNING")
                    if only_json:
                        self._log(f"⚠ {len(only_json)} IDs in JSON but not CSV", "WARNING")
        
        except Exception as e:
            self._log(f"Error checking consistency: {e}", "ERROR")
            self.issues.append(f"Consistency check error: {e}")
        
        self.results['consistency'] = checks
        return checks
    
    def print_summary(self) -> None:
        """Print comprehensive summary report"""
        self._log("\n" + "="*80, "INFO")
        self._log("DATA QUALITY REPORT SUMMARY", "INFO")
        self._log("="*80, "INFO")
        
        # Statistics
        total_checks = sum(len(v) for v in self.results.values() if isinstance(v, dict))
        
        self._log(f"\nReport generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self._log(f"Total checks performed: {total_checks}", "INFO")
        
        if self.issues:
            self._log(f"\n❌ ISSUES FOUND: {len(self.issues)}", "ERROR")
            for issue in self.issues:
                self._log(f"  - {issue}", "ERROR")
        
        if self.warnings:
            self._log(f"\n⚠️  WARNINGS: {len(self.warnings)}", "WARNING")
            for warning in self.warnings:
                self._log(f"  - {warning}", "WARNING")
        
        if not self.issues:
            self._log("\n✅ ALL CRITICAL CHECKS PASSED", "SUCCESS")
        
        self._log("\n" + "="*80, "INFO")
    
    def run(self) -> bool:
        """Run all verification checks"""
        self._log("\n" + "="*80, "INFO")
        self._log("DATA QUALITY VERIFICATION SYSTEM", "INFO")
        self._log("="*80, "INFO")
        
        # Run all checks
        self.connect_mongodb()
        self.verify_mongodb_data()
        self.verify_output_files()
        self.verify_data_consistency()
        
        # Print summary
        self.print_summary()
        
        return len(self.issues) == 0


def main():
    """Main entry point"""
    report = DataQualityReport()
    success = report.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
