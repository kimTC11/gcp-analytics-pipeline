"""
MongoDB Connection Module

This module provides utilities for connecting to MongoDB with proper
error handling, configuration management, and connection pooling.
"""

import os
import json
from typing import Optional, Union, Dict, List, Any
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from dotenv import load_dotenv


def get_mongodb_connection(
    uri: Optional[str] = None,
    database_name: Optional[str] = None,
    timeout: int = 5000
) -> tuple[Optional[MongoClient], Optional[str]]:
    """
    Connect to MongoDB instance.
    
    Args:
        uri: MongoDB connection URI. If not provided, loads from MONGODB_URI env var.
        database_name: Database name. If not provided, loads from MONGODB_DB env var.
        timeout: Connection timeout in milliseconds (default: 5000ms).
    
    Returns:
        Tuple of (MongoClient, database_name) on success, or (None, error_message) on failure.
    
    Example:
        client, db_name = get_mongodb_connection()
        if client:
            db = client[db_name]
            collection = db["my_collection"]
            print(collection.count_documents({}))
        else:
            print(f"Connection error: {db_name}")
    """
    # Load environment variables from .env file if present
    load_dotenv()
    
    # Get connection parameters
    connection_uri = uri or os.getenv("MONGODB_URI")
    db_name = database_name or os.getenv("MONGODB_DB")
    
    # Validate required parameters
    if not connection_uri:
        return None, "Error: MONGODB_URI not provided and not set in environment"
    
    if not db_name:
        return None, "Error: MONGODB_DB not provided and not set in environment"
    
    try:
        # Create MongoClient with timeout settings
        # socketTimeoutMS: timeout for operations (important for large queries)
        # connectTimeoutMS: timeout for establishing connection
        # serverSelectionTimeoutMS: timeout for server discovery
        client = MongoClient(
            connection_uri,
            serverSelectionTimeoutMS=timeout,
            connectTimeoutMS=timeout,
            socketTimeoutMS=timeout  # Increased to handle large collections
        )
        
        # Verify connection by pinging the server
        client.admin.command("ping")
        
        print(f"✓ Successfully connected to MongoDB (database: {db_name})")
        return client, db_name
        
    except ServerSelectionTimeoutError as e:
        error_msg = f"Connection timeout: Could not connect to MongoDB server within {timeout}ms"
        print(f"✗ {error_msg}")
        return None, error_msg
    
    except ConnectionFailure as e:
        error_msg = f"Connection failed: {str(e)}"
        print(f"✗ {error_msg}")
        return None, error_msg
    
    except Exception as e:
        error_msg = f"Unexpected error during connection: {str(e)}"
        print(f"✗ {error_msg}")
        return None, error_msg


def close_mongodb_connection(client: Optional[MongoClient]) -> bool:
    """
    Close MongoDB connection safely.
    
    Args:
        client: MongoClient instance to close.
    
    Returns:
        True if closed successfully, False otherwise.
    """
    if client is None:
        return True
    
    try:
        client.close()
        print("✓ MongoDB connection closed successfully")
        return True
    except Exception as e:
        print(f"✗ Error closing MongoDB connection: {str(e)}")
        return False


class MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle MongoDB ObjectId and other BSON types."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        from datetime import datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def clean_document_for_jsonl(doc: Dict) -> Dict:
    """
    Convert MongoDB document to clean JSON-serializable format for JSONL export.
    
    Converts:
    - ObjectId to string (e.g., "5ed8cb2bc671fc36b74653ad")
    - datetime objects to ISO format strings
    - Nested ObjectIds in lists and dicts
    
    Args:
        doc: MongoDB document dictionary
    
    Returns:
        Cleaned document safe for JSON serialization
    """
    from datetime import datetime
    
    if isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    elif isinstance(doc, dict):
        return {k: clean_document_for_jsonl(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [clean_document_for_jsonl(item) for item in doc]
    else:
        return doc


def export_mongodb_data(
    collection_names: Union[str, List[str]],
    database_name: str = "countly",
    output_path: Optional[str] = None,
    mongo_uri: Optional[str] = None,
    query_filter: Optional[Dict] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Export data from MongoDB collection(s) to JSONL files (JSON Lines format).
    
    JSONL format: Each line is a valid JSON object, ideal for streaming and large datasets.
    
    Args:
        collection_names: Single collection name (str) or list of collection names to export.
        database_name: Database name. Default is "countly".
        output_path: Output directory path. If None, uses ./exports/ directory.
        mongo_uri: MongoDB connection URI. If not provided, loads from MONGODB_URI env var.
        query_filter: Optional MongoDB query filter (e.g., {"status": "active"}).
        limit: Maximum number of documents to export per collection. If None, exports all.
    
    Returns:
        Dictionary with export results containing:
        - status: "success" or "error"
        - exported_collections: List of exported collections with document counts
        - output_files: Paths to exported JSONL files
        - total_documents: Total documents exported
        - timestamp: Export timestamp
        - error_message: Error message if failed
    
    Example:
        # Export single collection
        result = export_mongodb_data("summary")
        
        # Export multiple collections
        result = export_mongodb_data(["summary", "ip_locations"])
        
        # Export with custom output path and filter
        result = export_mongodb_data(
            collection_names="summary",
            output_path="/path/to/output",
            query_filter={"event_type": "purchase"},
            limit=1000
        )
    """
    from datetime import datetime
    
    # Normalize collection_names to list
    if isinstance(collection_names, str):
        collection_names = [collection_names]
    elif not isinstance(collection_names, list):
        return {
            "status": "error",
            "error_message": "collection_names must be a string or list of strings"
        }
    
    # Set default output path
    if output_path is None:
        output_path = "./exports"
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to MongoDB
    client, db_name = get_mongodb_connection(mongo_uri, database_name, timeout=10000)
    if client is None:
        return {
            "status": "error",
            "error_message": db_name  # db_name contains error message
        }
    
    try:
        db = client[database_name]
        exported_collections = []
        output_files = []
        total_documents = 0
        
        for collection_name in collection_names:
            try:
                collection = db[collection_name]
                
                # Get documents with optional filter and limit
                query = query_filter or {}
                documents = list(collection.find(query).limit(limit or 0))
                
                if not documents:
                    print(f"⚠️  No documents found in collection '{collection_name}'")
                    continue
                
                # Create output file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = output_dir / f"{collection_name}_{timestamp}.jsonl"
                
                # Export to JSONL (one JSON object per line)
                with open(output_file, 'w', encoding='utf-8') as f:
                    for doc in documents:
                        # Clean document: convert ObjectId to string, datetime to ISO format
                        clean_doc = clean_document_for_jsonl(doc)
                        json_line = json.dumps(clean_doc, ensure_ascii=False)
                        f.write(json_line + '\n')
                
                doc_count = len(documents)
                total_documents += doc_count
                output_files.append(str(output_file))
                
                exported_collections.append({
                    "collection_name": collection_name,
                    "document_count": doc_count,
                    "output_file": str(output_file)
                })
                
                print(f"✓ Exported '{collection_name}': {doc_count:,} documents → {output_file}")
            
            except Exception as e:
                error_msg = f"Error exporting collection '{collection_name}': {str(e)}"
                print(f"✗ {error_msg}")
                exported_collections.append({
                    "collection_name": collection_name,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "exported_collections": exported_collections,
            "output_files": output_files,
            "total_documents": total_documents,
            "timestamp": datetime.now().isoformat(),
            "output_directory": str(output_dir)
        }
    
    except Exception as e:
        error_msg = f"Unexpected error during export: {str(e)}"
        print(f"✗ {error_msg}")
        return {
            "status": "error",
            "error_message": error_msg
        }
    
    finally:
        close_mongodb_connection(client)


if __name__ == "__main__":
    # Test the connection
    print("Testing MongoDB Connection...")
    print("-" * 50)
    
    client, result = get_mongodb_connection()
    
    if client:
        db_name = result
        print(f"\nConnected to database: {db_name}")
        
        # List available databases
        try:
            admin_db = client["admin"]
            databases = client.list_database_names()
            print(f"Available databases: {len(databases)}")
            for db in databases[:5]:  # Show first 5
                print(f"  - {db}")
            if len(databases) > 5:
                print(f"  ... and {len(databases) - 5} more")
        except Exception as e:
            print(f"Error listing databases: {e}")
        
        # Close connection
        close_mongodb_connection(client)
    else:
        print(f"\n{result}")
    
    # Test export functionality
    print("\n" + "=" * 80)
    print("Testing MongoDB Export Function...")
    print("-" * 50)
    
    # Example 1: Export single collection with limit
    print("\n[Example 1] Exporting 'summary' collection (limit: 5 documents)...")
    result = export_mongodb_data(
        collection_names="summary",
        database_name="countly",
        output_path="./exports",
        limit=5
    )
    
    if result["status"] == "success":
        print(f"\n✓ Export successful!")
        print(f"  Total documents exported: {result['total_documents']}")
        print(f"  Output directory: {result['output_directory']}")
        for collection_info in result["exported_collections"]:
            print(f"  - {collection_info['collection_name']}: {collection_info['document_count']} documents")
    else:
        print(f"✗ Export failed: {result.get('error_message', 'Unknown error')}")
    
    # Example 2: Export multiple collections
    print("\n" + "-" * 50)
    print("[Example 2] Exporting multiple collections...")
    result = export_mongodb_data(
        collection_names=["summary", "ip_locations"],
        database_name="countly",
        output_path="./exports",
        limit=10
    )
    
    if result["status"] == "success":
        print(f"\n✓ Export successful!")
        print(f"  Total documents exported: {result['total_documents']}")
        for collection_info in result["exported_collections"]:
            if "error" not in collection_info:
                print(f"  - {collection_info['collection_name']}: {collection_info['document_count']} documents")
    else:
        print(f"✗ Export failed: {result.get('error_message', 'Unknown error')}")
