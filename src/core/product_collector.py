#!/usr/bin/env python
"""
Task 6: Product Information Collection (2 days)

Filters product-related events from MongoDB summary collection.
Extracts product IDs, URLs, and product names.
Stores results in JSON/CSV files for later transformation.

Data sources:
  - view_product_detail
  - select_product_option
  - select_product_option_quality
  - add_to_cart_action
  - product_detail_recommendation_visible
  - product_detail_recommendation_noticed
  - product_view_all_recommend_clicked (use referrer_url)

Output:
  - JSON file with structured product data
  - CSV file with product summary
"""

import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


class ProductCollector:
    """Collect and process product information from event data."""
    
    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017",
        db_name: str = "countly",
        source_collection: str = "summary",
    ):
        """Initialize the Product Collector."""
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.source_collection = source_collection
        self.client = None
        self.db = None
    
    def _log(self, msg: str) -> None:
        """Print message and flush for real-time output."""
        print(msg)
        sys.stdout.flush()
    
    def connect_mongodb(self) -> bool:
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[self.db_name]
            self.client.admin.command('ping')
            self._log(f"✓ Connected to MongoDB: {self.mongo_uri}")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self._log(f"✗ MongoDB connection failed: {e}")
            return False
    
    def extract_product_data(self) -> Dict[str, Dict]:
        """
        Extract product data from summary collection.
        
        Returns:
            Dictionary mapping product_id to product data
        """
        # Event types to process
        event_types = {
            "view_product_detail",
            "select_product_option",
            "select_product_option_quality",
            "add_to_cart_action",
            "product_detail_recommendation_visible",
            "product_detail_recommendation_noticed",
            "product_view_all_recommend_clicked",
        }
        
        collection = self.db[self.source_collection]
        
        self._log(f"\nExtracting product data from '{self.source_collection}' collection...")
        self._log(f"Event types: {', '.join(event_types)}\n")
        
        # Build product dictionary with aggregation
        products = {}
        processed = 0
        
        # Create pipeline to filter and extract product data
        pipeline = [
            {"$match": {"collection": {"$in": list(event_types)}}},
            {
                "$project": {
                    "collection": 1,
                    "product_id": 1,
                    "viewing_product_id": 1,
                    "current_url": 1,
                    "referrer_url": 1,
                    "time_stamp": 1,
                }
            },
            {"$sort": {"time_stamp": -1}},  # Latest first
        ]
        
        cursor = collection.aggregate(pipeline, allowDiskUse=True, batchSize=1000)
        
        for doc in cursor:
            processed += 1
            
            if processed % 100000 == 0:
                self._log(f"  Progress: {processed:,} records processed | {len(products):,} unique products found")
            
            # Determine product_id
            product_id = doc.get("product_id") or doc.get("viewing_product_id") or doc.get("recommendation_product_id")
            
            if not product_id:
                continue
            
            product_id = str(product_id)
            
            # Determine URL
            url = None
            if doc.get("collection") == "product_view_all_recommend_clicked":
                url = doc.get("referrer_url")
            else:
                url = doc.get("current_url")
            
            if not url:
                continue
            
            # Store/update product data (keep only one entry per product_id)
            if product_id not in products:
                products[product_id] = {
                    "product_id": product_id,
                    "url": url,
                    "event_type": doc.get("collection"),
                    "timestamp": doc.get("time_stamp"),
                    "product_name": None,
                }
        
        self._log(f"\n✓ Extraction complete:")
        self._log(f"  Total records processed: {processed:,}")
        self._log(f"  Unique products found: {len(products):,}")
        
        return products
    
    def extract_product_name_from_url(self, url: str) -> Optional[str]:
        """
        Extract product name from URL.
        
        Args:
            url: Product URL
            
        Returns:
            Product name or None
        """
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Extract from /product/NAME or /products/NAME
            if "/product" in path:
                for pattern in ["/product/", "/products/"]:
                    if pattern in path:
                        parts = path.split(pattern)
                        if len(parts) > 1:
                            name = parts[1].split("/")[0].split("?")[0].split(".")[0]
                            if name:
                                return name.replace("-", " ").replace("_", " ")
            
            # Try last path segment
            segments = path.strip("/").split("/")
            if segments and segments[-1]:
                name = segments[-1].split("?")[0].split(".")[0]
                if name:
                    return name.replace("-", " ").replace("_", " ")
            
            return None
        except Exception:
            return None
    
    def enrich_products_with_names(self, products: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Enrich product data with extracted names from URLs.
        
        Args:
            products: Product data dictionary
            
        Returns:
            Enriched product data
        """
        self._log(f"\nExtracting product names from URLs...")
        
        success = 0
        failed = 0
        
        for i, (product_id, data) in enumerate(products.items(), 1):
            if i % 100000 == 0:
                self._log(f"  Progress: {i:,}/{len(products):,} | Success: {success:,} | Failed: {failed:,}")
            
            if data["url"]:
                name = self.extract_product_name_from_url(data["url"])
                if name:
                    data["product_name"] = name
                    success += 1
                else:
                    failed += 1
            else:
                failed += 1
        
        self._log(f"\n✓ Name extraction complete:")
        self._log(f"  Successfully extracted: {success:,}")
        self._log(f"  Failed to extract: {failed:,}")
        
        return products
    
    def save_to_json(self, products: Dict[str, Dict], output_path: str) -> bool:
        """Save products to JSON file."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            
            self._log(f"✓ JSON file saved: {output_path}")
            return True
        except Exception as e:
            self._log(f"✗ Error saving JSON: {e}")
            return False
    
    def save_to_csv(self, products: Dict[str, Dict], output_path: str) -> bool:
        """Save products to CSV file."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            fieldnames = ["product_id", "product_name", "url", "event_type", "timestamp"]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for product_id, data in sorted(products.items()):
                    writer.writerow({
                        "product_id": data["product_id"],
                        "product_name": data.get("product_name") or "",
                        "url": data.get("url") or "",
                        "event_type": data.get("event_type") or "",
                        "timestamp": data.get("timestamp") or "",
                    })
            
            self._log(f"✓ CSV file saved: {output_path}")
            return True
        except Exception as e:
            self._log(f"✗ Error saving CSV: {e}")
            return False
    
    def process_products(
        self,
        output_json: str,
        output_csv: str,
    ) -> Dict:
        """
        Main processing function.
        
        Args:
            output_json: Output JSON file path
            output_csv: Output CSV file path
            
        Returns:
            Statistics dictionary
        """
        # Step 1: Extract product data
        products = self.extract_product_data()
        
        # Step 2: Enrich with product names
        products = self.enrich_products_with_names(products)
        
        # Step 3: Save to files
        json_saved = self.save_to_json(products, output_json)
        csv_saved = self.save_to_csv(products, output_csv)
        
        stats = {
            "status": "completed" if json_saved and csv_saved else "partial",
            "total_products": len(products),
            "with_product_name": sum(1 for p in products.values() if p.get("product_name")),
            "without_product_name": sum(1 for p in products.values() if not p.get("product_name")),
            "output_json": output_json if json_saved else None,
            "output_csv": output_csv if csv_saved else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return stats
    
    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._log("✓ MongoDB connection closed")


def main():
    """Main execution for Task 6."""
    
    # Configuration
    MONGO_URI = "mongodb://localhost:27017"
    DB_NAME = "countly"
    SOURCE_COLLECTION = "summary"
    OUTPUT_JSON = "/home/tuancuong112504/prj5-gcp/output/products.json"
    OUTPUT_CSV = "/home/tuancuong112504/prj5-gcp/output/products.csv"
    
    print("\n" + "=" * 80)
    print("TASK 6: Product Information Collection")
    print("=" * 80)
    print("")
    print("Configuration:")
    print(f"  MongoDB URI: {MONGO_URI}")
    print(f"  Database: {DB_NAME}")
    print(f"  Source Collection: {SOURCE_COLLECTION}")
    print(f"  Output JSON: {OUTPUT_JSON}")
    print(f"  Output CSV: {OUTPUT_CSV}")
    print("")
    
    collector = ProductCollector(
        mongo_uri=MONGO_URI,
        db_name=DB_NAME,
        source_collection=SOURCE_COLLECTION,
    )
    
    try:
        # Connect to MongoDB
        if not collector.connect_mongodb():
            return False
        
        # Process products
        stats = collector.process_products(
            output_json=OUTPUT_JSON,
            output_csv=OUTPUT_CSV,
        )
        
        # Display results
        print("\n" + "=" * 80)
        print("✅ PROCESSING COMPLETE")
        print("=" * 80)
        print(f"Status: {stats['status']}")
        print(f"Total products extracted: {stats['total_products']:,}")
        print(f"  With product name: {stats['with_product_name']:,}")
        print(f"  Without product name: {stats['without_product_name']:,}")
        print(f"\nOutput files:")
        if stats['output_json']:
            print(f"  JSON: {stats['output_json']}")
        if stats['output_csv']:
            print(f"  CSV: {stats['output_csv']}")
        print(f"\nProcessed at: {stats['timestamp']}")
        print("=" * 80 + "\n")
        
        return True
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user (Ctrl+C)")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    
    finally:
        collector.close()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
