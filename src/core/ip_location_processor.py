"""
IP Location Processing Module
Reads unique IPs from MongoDB, enriches with location data using ip2location BIN file,
and stores results in MongoDB collection and CSV file.
"""

import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import IP2Location


class IPLocationProcessor:
    """Process IP addresses and enrich them with location data."""
    
    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017",
        db_name: str = "ip_data",
        bin_file_path: str = None,
    ):
        """
        Initialize the IP Location Processor.
        
        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
            bin_file_path: Path to IP2Location BIN file
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.bin_file_path = bin_file_path or self._find_bin_file()
        self.client = None
        self.db = None
        self.ip2location = None
    
    def _log(self, msg: str) -> None:
        """Print message and flush for real-time output."""
        print(msg)
        sys.stdout.flush()
        
    def _find_bin_file(self) -> str:
        """Auto-detect BIN file location."""
        search_paths = [
            Path("/home/tuancuong112504/prj5-gcp/monggodb-data/IP-COUNTRY-REGION-CITY.BIN"),
            Path("./monggodb-data/IP-COUNTRY-REGION-CITY.BIN"),
            Path("../monggodb-data/IP-COUNTRY-REGION-CITY.BIN"),
            Path("./IP-COUNTRY-REGION-CITY.BIN"),
        ]
        
        for path in search_paths:
            if path.exists():
                self._log(f"✓ Found BIN file: {path}")
                return str(path)
        
        raise FileNotFoundError(
            "IP2Location BIN file not found. Please provide bin_file_path parameter."
        )
    
    def connect_mongodb(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[self.db_name]
            # Verify connection
            self.client.admin.command('ping')
            self._log(f"✓ Connected to MongoDB: {self.mongo_uri}")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self._log(f"✗ MongoDB connection failed: {e}")
            return False
    
    def load_ip2location(self) -> bool:
        """
        Load IP2Location database.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.bin_file_path):
                self._log(f"✗ BIN file not found: {self.bin_file_path}")
                return False
            
            self.ip2location = IP2Location.IP2Location(self.bin_file_path)
            self._log(f"✓ IP2Location database loaded: {self.bin_file_path}")
            return True
        except Exception as e:
            self._log(f"✗ Failed to load IP2Location database: {e}")
            return False
    
    def get_unique_ips(self, source_collection: str = "raw_data", batch_size: int = 10000) -> List[str]:
        """
        Read unique IPs from source collection (optimized for large datasets).
        
        Args:
            source_collection: Name of the source collection
            batch_size: Batch size for processing
            
        Returns:
            List of unique IP addresses
        """
        try:
            collection = self.db[source_collection]
            
            # Check if index exists, create if not
            indexes = collection.list_indexes()
            index_names = [idx['name'] for idx in indexes]
            if 'ip_1' not in index_names:
                self._log("  Creating index on 'ip' field (this may take a while for large datasets)...")
                collection.create_index("ip")
            
            self._log("  Extracting unique IPs (this may take a while for large datasets)...")
            
            # Get unique IPs using aggregation pipeline with disk usage allowed
            pipeline = [
                {"$match": {"ip": {"$exists": True, "$ne": None, "$ne": ""}}},
                {"$group": {"_id": "$ip"}},
                {"$project": {"_id": 0, "ip": "$_id"}},
                {"$sort": {"ip": 1}},
            ]
            
            cursor = collection.aggregate(pipeline, allowDiskUse=True, batchSize=batch_size)
            
            unique_ips = []
            for i, doc in enumerate(cursor, 1):
                unique_ips.append(doc["ip"])
                if i % 100000 == 0:
                    self._log(f"    Progress: {i:,} unique IPs found...")
            
            self._log(f"✓ Found {len(unique_ips):,} unique IPs in collection '{source_collection}'")
            return unique_ips
        except Exception as e:
            self._log(f"✗ Error reading IPs: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def lookup_ip(self, ip: str) -> Optional[Dict]:
        """
        Lookup IP address information.
        
        Args:
            ip: IP address to lookup
            
        Returns:
            Dictionary with location data or None
        """
        try:
            rec = self.ip2location.get_all(ip)
            
            if rec is None:
                return None
            
            return {
                "ip": ip,
                "country_code": rec.country_short,
                "country_name": rec.country_long,
                "region_name": rec.region,
                "city_name": rec.city,
                "latitude": rec.latitude,
                "longitude": rec.longitude,
                "zip_code": rec.zipcode,
                "time_zone": rec.timezone,
                "isp": rec.isp or "",
                "domain": rec.domain or "",
                "net_speed": rec.netspeed or "",
                "idd_code": rec.idd_code or "",
                "area_code": rec.area_code or "",
                "weather_station_code": rec.weather_code or "",
                "weather_station_name": rec.weather_name or "",
                "mcc": rec.mcc or "",
                "mnc": rec.mnc or "",
                "mobile_brand": rec.mobile_brand or "",
                "elevation": rec.elevation or 0,
                "usage_type": rec.usage_type or "",
                "processed_at": datetime.utcnow(),
            }
        except Exception as e:
            self._log(f"✗ Error looking up IP {ip}: {e}")
            return None
    
    def process_ip_locations(
        self,
        source_collection: str = "raw_data",
        output_collection: str = "ip_locations",
        output_csv: str = None,
        chunk_size: int = 1000,
    ) -> Dict:
        """
        Process all unique IPs and store results (optimized for large datasets).
        
        Args:
            source_collection: Source collection name
            output_collection: Output collection name for MongoDB
            output_csv: Output CSV file path (optional)
            chunk_size: Number of IPs to process before writing batch to MongoDB
            
        Returns:
            Dictionary with processing statistics
        """
        # Get unique IPs
        unique_ips = self.get_unique_ips(source_collection)
        if not unique_ips:
            return {"status": "failed", "message": "No IPs found to process"}
        
        # Initialize output collection
        output_coll = self.db[output_collection]
        output_coll.create_index("ip", unique=True)
        
        # Process IPs in batches
        results = []
        successful = 0
        failed = 0
        
        self._log(f"\nProcessing {len(unique_ips):,} IPs in batches of {chunk_size}...")
        self._log("(Large datasets may take significant time - processor will show progress every 1000 IPs)")
        
        for i, ip in enumerate(unique_ips, 1):
            if i % 1000 == 0:
                elapsed_percent = (i / len(unique_ips)) * 100
                self._log(f"  Progress: {i:,}/{len(unique_ips):,} ({elapsed_percent:.1f}%) | Successful: {successful:,} | Failed: {failed:,}")
            
            location_data = self.lookup_ip(ip)
            
            if location_data:
                # Upsert to MongoDB
                try:
                    output_coll.update_one(
                        {"ip": ip},
                        {"$set": location_data},
                        upsert=True
                    )
                    results.append(location_data)
                    successful += 1
                except Exception as e:
                    self._log(f"    Error storing IP {ip}: {e}")
                    failed += 1
            else:
                failed += 1
            
            # Batch write CSV every chunk_size records
            if output_csv and len(results) >= chunk_size:
                self._write_csv_batch(results, output_csv, append=(i > chunk_size))
                results = []
        
        # Write remaining results to CSV
        if output_csv and results:
            self._write_csv_batch(results, output_csv, append=(len(unique_ips) > chunk_size))
        
        stats = {
            "status": "completed",
            "total_processed": len(unique_ips),
            "successful": successful,
            "failed": failed,
            "output_collection": output_collection,
            "output_csv": output_csv,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self._log(f"\n✓ Processing complete:")
        self._log(f"  Total: {stats['total_processed']:,}")
        self._log(f"  Successful: {stats['successful']:,}")
        self._log(f"  Failed: {stats['failed']:,}")
        
        return stats
    
    def _write_csv(self, results: List[Dict], output_path: str) -> None:
        """
        Write results to CSV file.
        
        Args:
            results: List of location data dictionaries
            output_path: Output file path
        """
        if not results:
            self._log(f"No results to write to CSV")
            return
        
        try:
            # Create directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            fieldnames = list(results[0].keys())
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            self._log(f"✓ CSV file written: {output_path}")
        except Exception as e:
            self._log(f"✗ Error writing CSV: {e}")
    
    def _write_csv_batch(self, results: List[Dict], output_path: str, append: bool = False) -> None:
        """
        Write results to CSV file in batch mode (append or create).
        
        Args:
            results: List of location data dictionaries
            output_path: Output file path
            append: Whether to append to existing file
        """
        if not results:
            return
        
        try:
            # Create directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            fieldnames = list(results[0].keys())
            file_exists = Path(output_path).exists() and append
            
            mode = 'a' if file_exists else 'w'
            with open(output_path, mode, newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(results)
        except Exception as e:
            self._log(f"✗ Error writing CSV batch: {e}")
    
    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._log("✓ MongoDB connection closed")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process IP addresses and enrich with location data"
    )
    parser.add_argument(
        "--mongo-uri",
        default="mongodb://localhost:27017",
        help="MongoDB connection URI (default: mongodb://localhost:27017)",
    )
    parser.add_argument(
        "--db-name",
        default="ip_data",
        help="Database name (default: ip_data)",
    )
    parser.add_argument(
        "--bin-file",
        help="Path to IP2Location BIN file (auto-detected if not provided)",
    )
    parser.add_argument(
        "--source-collection",
        default="raw_data",
        help="Source collection name (default: raw_data)",
    )
    parser.add_argument(
        "--output-collection",
        default="ip_locations",
        help="Output collection name (default: ip_locations)",
    )
    parser.add_argument(
        "--output-csv",
        help="Output CSV file path (optional)",
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = IPLocationProcessor(
        mongo_uri=args.mongo_uri,
        db_name=args.db_name,
        bin_file_path=args.bin_file,
    )
    
    try:
        # Connect to MongoDB
        if not processor.connect_mongodb():
            return
        
        # Load IP2Location database
        if not processor.load_ip2location():
            return
        
        # Process IPs
        stats = processor.process_ip_locations(
            source_collection=args.source_collection,
            output_collection=args.output_collection,
            output_csv=args.output_csv,
        )
        
        print(f"\nStatistics: {stats}")
    
    finally:
        processor.close()


if __name__ == "__main__":
    main()
