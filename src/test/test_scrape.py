#!/usr/bin/env python3
"""
Test: Product Name Scraper and Consolidator

Crawls product names from the existing dataset.
Gets only ONE active product name per product_id.
Prints results to terminal.
"""

import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ProductScrapeTest:
    """Test product scraping and consolidation"""
    
    def __init__(self):
        self.csv_path = Path(__file__).parent.parent.parent / "output" / "products.csv"
        self.json_path = Path(__file__).parent.parent.parent / "output" / "products.json"
        self.products_by_id = defaultdict(list)
        self.consolidated_products = {}
        
    def _log(self, msg: str, level: str = "INFO") -> None:
        """Print message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level:8} | {msg}")
        sys.stdout.flush()
    
    def _is_valid_product_name(self, name: str) -> bool:
        """
        Check if name is a valid product name (not just an ID)
        
        Valid: Contains letters, not just numbers
        Invalid: Pure numeric strings or too short
        """
        if not name or len(name) < 2:
            return False
        
        # Check if string contains at least one letter
        has_letter = any(c.isalpha() for c in name.lower())
        return has_letter
    
    def _get_active_product_name(self, names: List[str]) -> Tuple[str, bool]:
        """
        Select the best active product name from list
        
        Priority:
        1. Valid product name (contains letters) - most recent
        2. Any available name
        
        Returns: (product_name, is_valid)
        """
        # Filter for valid names (containing letters, not just IDs)
        valid_names = [n for n in names if self._is_valid_product_name(n)]
        
        if valid_names:
            # Return the first valid name (most recent due to reverse sorting)
            return valid_names[0], True
        elif names:
            # Fallback to first available name
            return names[0], False
        else:
            return "", False
    
    def load_from_csv(self) -> int:
        """Load products from CSV file"""
        if not self.csv_path.exists():
            self._log(f"CSV file not found: {self.csv_path}", "WARN")
            return 0
        
        self._log(f"Loading from CSV: {self.csv_path}")
        count = 0
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    product_id = row.get('product_id', '').strip()
                    product_name = row.get('product_name', '').strip()
                    url = row.get('url', '').strip()
                    event_type = row.get('event_type', '').strip()
                    timestamp = row.get('timestamp', '').strip()
                    
                    if product_id and product_name:
                        self.products_by_id[product_id].append({
                            'name': product_name,
                            'url': url,
                            'event_type': event_type,
                            'timestamp': int(timestamp) if timestamp else 0
                        })
                        count += 1
            
            self._log(f"✓ Loaded {count:,} records from CSV")
            return count
        
        except Exception as e:
            self._log(f"✗ Error loading CSV: {e}", "ERROR")
            return 0
    
    def load_from_json(self) -> int:
        """Load products from JSON file"""
        if not self.json_path.exists():
            self._log(f"JSON file not found: {self.json_path}", "WARN")
            return 0
        
        self._log(f"Loading from JSON: {self.json_path}")
        count = 0
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for product_id, product_data in data.items():
                    product_name = product_data.get('product_name', '').strip()
                    url = product_data.get('url', '').strip()
                    event_type = product_data.get('event_type', '').strip()
                    timestamp = product_data.get('timestamp', 0)
                    
                    if product_id and product_name:
                        # Store (deduplicate will happen later)
                        self.products_by_id[product_id].append({
                            'name': product_name,
                            'url': url,
                            'event_type': event_type,
                            'timestamp': timestamp
                        })
                        count += 1
            
            self._log(f"✓ Loaded {count:,} records from JSON")
            return count
        
        except Exception as e:
            self._log(f"✗ Error loading JSON: {e}", "ERROR")
            return 0
    
    def consolidate_products(self) -> int:
        """
        Get one active product name per product_id
        
        Selects the best available name based on validity and recency
        """
        self._log(f"\nConsolidating products (keeping 1 per product_id)...")
        
        count = 0
        for product_id, records in self.products_by_id.items():
            if not records:
                continue
            
            # Sort by timestamp descending (most recent first)
            sorted_records = sorted(records, key=lambda x: x['timestamp'], reverse=True)
            
            # Get unique names from sorted records
            unique_names = []
            seen = set()
            for record in sorted_records:
                name = record['name']
                if name not in seen:
                    unique_names.append(name)
                    seen.add(name)
            
            # Select the best active product name
            active_name, is_valid = self._get_active_product_name(unique_names)
            
            if active_name:
                # Store the consolidated product
                self.consolidated_products[product_id] = {
                    'product_id': product_id,
                    'product_name': active_name,
                    'is_active': is_valid,
                    'url': sorted_records[0]['url'],
                    'event_type': sorted_records[0]['event_type'],
                    'timestamp': sorted_records[0]['timestamp'],
                    'variants_count': len(unique_names)
                }
                count += 1
        
        self._log(f"✓ Consolidated {count:,} unique products")
        return count
    
    def print_results(self) -> None:
        """Print results to terminal"""
        self._log("\n" + "="*100)
        self._log("ACTIVE PRODUCTS (One per product_id)", "RESULT")
        self._log("="*100)
        
        # Sort by product_id
        sorted_products = sorted(self.consolidated_products.items(), key=lambda x: int(x[0]))
        
        # Print header
        header = f"{'Product ID':>12} | {'Product Name':<40} | {'Status':<8} | {'Variants':>8} | {'Event Type':<25}"
        print(f"\n{header}")
        print("-" * 100)
        
        # Print each product
        for product_id, data in sorted_products:
            status = "✓ ACTIVE" if data['is_active'] else "⚠ FALLBACK"
            variants = data['variants_count']
            event_type = data['event_type']
            product_name = data['product_name'][:40]
            
            print(f"{product_id:>12} | {product_name:<40} | {status:<8} | {variants:>8} | {event_type:<25}")
        
        # Print summary
        print("\n" + "-" * 100)
        total = len(self.consolidated_products)
        active = sum(1 for p in self.consolidated_products.values() if p['is_active'])
        fallback = total - active
        
        summary = f"\nTotal: {total:,} | Active Names: {active:,} | Fallback IDs: {fallback:,}"
        print(summary)
        
        self._log("="*100)
    
    def run(self) -> bool:
        """Execute the test"""
        try:
            self._log("Starting Product Scrape Test...")
            self._log("-" * 100)
            
            # Load data
            csv_count = self.load_from_csv()
            json_count = self.load_from_json()
            
            total_loaded = csv_count + json_count
            if total_loaded == 0:
                self._log("✗ No data loaded from CSV or JSON", "ERROR")
                return False
            
            # Get unique product IDs
            unique_ids = len(self.products_by_id)
            self._log(f"\nTotal unique product_ids: {unique_ids:,}")
            
            # Consolidate
            consolidated = self.consolidate_products()
            
            # Print results
            self.print_results()
            
            # Save consolidated to JSON
            self.save_consolidated()
            
            self._log("✓ Test completed successfully!", "SUCCESS")
            return True
        
        except Exception as e:
            self._log(f"✗ Test failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def save_consolidated(self) -> None:
        """Save consolidated products to file"""
        try:
            output_path = Path(__file__).parent.parent.parent / "output" / "products_consolidated.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.consolidated_products, f, indent=2, ensure_ascii=False)
            
            self._log(f"✓ Saved consolidated products to: {output_path}", "SUCCESS")
        
        except Exception as e:
            self._log(f"✗ Error saving consolidated products: {e}", "ERROR")


def main():
    """Main entry point"""
    tester = ProductScrapeTest()
    success = tester.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
