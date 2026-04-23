# IP Location Processing

This module enriches IP addresses with location data using the IP2Location BIN database and stores results in MongoDB and CSV files.

## Features

✓ Read unique IPs from MongoDB collection
✓ Lookup location data using IP2Location BIN file
✓ Store results in MongoDB collection with unique IP index
✓ Export results to CSV file
✓ Auto-detect IP2Location BIN file location
✓ Command-line interface with flexible options
✓ Detailed processing statistics
✓ Error handling and progress reporting

## Installation

Using `uv`:

```bash
cd /home/tuancuong112504/prj5-gcp/source
uv pip install -r pyproject.toml
```

Or install dependencies manually:

```bash
uv pip install ip2location pymongo python-dotenv
```

## Usage

### Command Line

Basic usage (processes from `raw_data` collection):
```bash
python ip_location_processor.py
```

With custom options:
```bash
python ip_location_processor.py \
  --mongo-uri mongodb://localhost:27017 \
  --db-name ip_data \
  --source-collection raw_data \
  --output-collection ip_locations \
  --output-csv ./output/ip_locations.csv
```

All options:
```
--mongo-uri        MongoDB connection URI (default: mongodb://localhost:27017)
--db-name          Database name (default: ip_data)
--bin-file         Path to IP2Location BIN file (auto-detected if not provided)
--source-collection Source collection name (default: raw_data)
--output-collection Output collection name (default: ip_locations)
--output-csv       Output CSV file path (optional)
```

### Python API

```python
from ip_location_processor import IPLocationProcessor

# Initialize processor (auto-detects BIN file)
processor = IPLocationProcessor()

try:
    # Connect to MongoDB
    processor.connect_mongodb()
    
    # Load IP2Location database
    processor.load_ip2location()
    
    # Process IPs
    stats = processor.process_ip_locations(
        source_collection="raw_data",
        output_collection="ip_locations",
        output_csv="./output/ip_locations.csv"
    )
finally:
    processor.close()
```

### Single IP Lookup

```python
processor = IPLocationProcessor()
processor.load_ip2location()

result = processor.lookup_ip("8.8.8.8")
if result:
    print(f"Country: {result['country_name']}")
    print(f"City: {result['city_name']}")
    print(f"Coordinates: ({result['latitude']}, {result['longitude']})")
```

## Data Files

**IP2Location BIN File Location:**
```
/home/tuancuong112504/prj5-gcp/monggodb-data/IP-COUNTRY-REGION-CITY.BIN
```

The BIN file contains IP geolocation data and is automatically detected by the processor.

## Output

### MongoDB Collection Schema

Documents stored in the output collection include:

```json
{
  "_id": "ObjectId",
  "ip": "8.8.8.8",
  "country_code": "US",
  "country_name": "United States",
  "region_name": "California",
  "city_name": "Mountain View",
  "latitude": 37.405992,
  "longitude": -122.078515,
  "zip_code": "94043",
  "time_zone": "UTC-08:00",
  "isp": "Google LLC",
  "domain": "google.com",
  "net_speed": "T1",
  "idd_code": "1",
  "area_code": "650",
  "weather_station_code": "USCA0746",
  "weather_station_name": "Mountain View",
  "mcc": "",
  "mnc": "",
  "mobile_brand": "",
  "elevation": 0,
  "usage_type": "DCH",
  "processed_at": "2026-04-21T10:30:45.123456"
}
```

### CSV Export

CSV file with all location data in columnar format, including headers.

## Example Scripts

See `example_usage.py` for complete examples:

```bash
python example_usage.py
```

This demonstrates:
1. Single IP lookups
2. Basic MongoDB processing
3. Custom configuration

## Requirements

- Python 3.8+
- MongoDB (optional, for storing results)
- ip2location library
- pymongo library
- IP2Location BIN database file

## Performance Notes

- Process time depends on:
  - Number of unique IPs to process
  - IP2Location BIN file I/O speed
  - MongoDB write performance
  - Network latency
  
- For ~10,000 IPs: typically 10-30 seconds
- For ~100,000 IPs: typically 2-5 minutes

## Troubleshooting

**BIN file not found:**
- Ensure the file exists at `/home/tuancuong112504/prj5-gcp/monggodb-data/IP-COUNTRY-REGION-CITY.BIN`
- Or provide explicit path via `--bin-file` parameter

**MongoDB connection failed:**
- Ensure MongoDB is running: `mongosh` should connect
- Check connection URI in parameters
- Verify database credentials if using authentication

**Processing is slow:**
- Consider running in batches if database is very large
- Use SSD for faster file I/O
- Increase MongoDB batch write size

## License

This module is part of the IP Data Processing project.
