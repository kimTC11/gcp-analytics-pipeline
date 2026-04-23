# Data Structure Documentation

Complete reference of all data structures, collections, and formats used in the pipeline.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [MongoDB Collections](#mongodb-collections)
3. [CSV Output Format](#csv-output-format)
4. [JSON Output Format](#json-output-format)
5. [Data Relationships](#data-relationships)
6. [Field Definitions](#field-definitions)
7. [Data Quality Standards](#data-quality-standards)

---

## Overview

The pipeline processes event data from MongoDB and generates standardized output in both CSV and JSON formats.

**Processing Stages:**
1. **Source**: MongoDB `summary` collection (41.4M+ documents)
2. **Extraction**: Extract IP addresses and product information
3. **Enrichment**: Augment with geolocation and product details
4. **Output**: CSV and JSON files with processed data

---

## MongoDB Collections

### Source Collection: `summary`

**Purpose**: Raw event data from Countly analytics

**Document Structure** (sample):
```json
{
  "_id": ObjectId("..."),
  "collection": "view_product_detail",
  "ip": "192.168.1.1",
  "time_stamp": 1591256275,
  "product_id": "100000",
  "current_url": "https://glamira.com/product",
  "device": "desktop",
  "country": "RO",
  // ... additional fields ...
}
```

**Key Fields:**
- `_id` - MongoDB ObjectId
- `collection` - Event type
- `ip` - IP address (string)
- `time_stamp` - Unix timestamp
- `product_id` - Product identifier
- `current_url` - Page URL
- `device` - Device type (mobile/desktop)
- `country` - Country code (2-letter)

**Size**: ~41.4 million documents

---

### Generated Collection: `ip_locations`

**Purpose**: Enriched IP data with geolocation information

**Document Structure** (sample):
```json
{
  "_id": ObjectId("..."),
  "ip": "192.168.1.1",
  "country": "RO",
  "country_name": "Romania",
  "region": "Bucharest",
  "city": "Bucharest",
  "latitude": 44.4268,
  "longitude": 26.1025,
  "isp": "ISP Name",
  "processed_at": ISODate("2026-04-23T..."),
  "first_seen": 1591200000,
  "last_seen": 1591300000,
  "count": 1542
}
```

**Key Fields:**
- `ip` - IP address
- `country` - Country code
- `country_name` - Full country name
- `region` - State/province
- `city` - City name
- `latitude` / `longitude` - Geographic coordinates
- `isp` - Internet Service Provider
- `processed_at` - Processing timestamp
- `count` - Number of occurrences

**Size**: 3.2M+ unique IP addresses

---

## CSV Output Format

### products.csv

**Location**: `output/products.csv`

**Columns**:
```
product_id,product_name,url,event_type,timestamp
```

**Sample Data**:
```csv
100000,2248857,https://www.glamira.se/checkout/cart/configure/id/2248857/?alloy=white-585&diamond=emerald,view_product_detail,1591256275
100001,glamira ring orva,https://www.glamira.ro/glamira-ring-orva.html?alloy=white-585&stone2=diamond-sapphire,select_product_option_quality,1591224979
100002,glamira ring palmier,https://www.glamira.fr/glamira-ring-palmier.html?diamond=diamond-Swarovsky,select_product_option,1591261392
```

**Field Definitions**:
- **product_id** - Unique product identifier (integer)
- **product_name** - Product name (string, may contain descriptive text)
- **url** - Product page URL (string, may include query parameters)
- **event_type** - Type of event (string):
  - `view_product_detail` - Page view
  - `select_product_option` - Option selected
  - `select_product_option_quality` - Quality selection
  - `add_to_cart_action` - Add to cart
  - `product_detail_recommendation_visible` - Recommendation shown
  - `product_detail_recommendation_noticed` - Recommendation clicked
- **timestamp** - Unix timestamp (integer, seconds since 1970)

**Statistics**:
- **Total Records**: 19,417
- **Unique Products**: 19,417
- **File Size**: ~2-3 MB
- **Date Range**: June 2020 to present

---

### ip_locations.csv

**Location**: `log/ip_locations.csv`

**Columns**:
```
ip,country,region,city,latitude,longitude,isp,count,first_seen,last_seen
```

**Sample Data**:
```csv
192.168.1.1,RO,Bucharest,Bucharest,44.4268,26.1025,ISP Name,1542,1591200000,1591300000
203.0.113.45,US,California,San Francisco,37.7749,-122.4194,Another ISP,2103,1590500000,1592000000
```

**Field Definitions**:
- **ip** - IP address (string, format: xxx.xxx.xxx.xxx)
- **country** - Country code (string, 2-letter ISO code)
- **region** - State/province/region (string)
- **city** - City name (string)
- **latitude** - Latitude coordinate (float, -90 to 90)
- **longitude** - Longitude coordinate (float, -180 to 180)
- **isp** - Internet Service Provider name (string)
- **count** - Number of times IP was seen (integer)
- **first_seen** - First occurrence timestamp (integer)
- **last_seen** - Last occurrence timestamp (integer)

**Statistics**:
- **Total Unique IPs**: 3.2M+
- **Countries**: 195+
- **File Size**: ~150-200 MB

---

## JSON Output Format

### products.json

**Location**: `output/products.json`

**Structure**: Dictionary with product_id as key

**Sample Data**:
```json
{
  "100000": {
    "product_id": "100000",
    "product_name": "Engagement Ring Lucetta",
    "url": "https://www.glamira.com/catalog/product/view/id/100000",
    "event_type": "view_product_detail",
    "timestamp": 1591256275,
    "sku": "Ophelia-Ring",
    "price": "1758.00",
    "product_type": "ring",
    "gender": "women",
    "collection": "vintage"
  },
  "100001": {
    "product_id": "100001",
    "product_name": "Inel de Logodnă Orva",
    "url": "https://www.glamira.ro/glamira-ring-orva.html",
    "event_type": "select_product_option_quality",
    "timestamp": 1591224979,
    // ... more fields ...
  }
}
```

**Document Fields**:
- **product_id** - Unique identifier
- **product_name** - Product name (string)
- **url** - Product page URL
- **event_type** - Type of user event
- **timestamp** - Event timestamp
- **sku** - Stock keeping unit
- **price** - Product price
- **product_type** - Category (ring, pendant, earring, bracelet, kids, etc.)
- **gender** - Target gender (women, men, unisex)
- **collection** - Product collection name
- **crawled_at** - When data was crawled (ISO format)

**Statistics**:
- **Total Products**: 19,417
- **File Size**: ~50-70 MB
- **Indentation**: 2 spaces for readability

---

## Data Relationships

### Event Type Mapping

```
MongoDB Event Types → Data Pipeline:

view_product_detail
├─ Source: Page view events
├─ Contains: product_id, URL
└─ Count: ~8.2M events

select_product_option
├─ Source: Option selection
├─ Contains: product_id, selected options
└─ Count: ~5.1M events

select_product_option_quality
├─ Source: Quality/variant selection
├─ Contains: product_id, quality choice
└─ Count: ~3.4M events

add_to_cart_action
├─ Source: Cart addition
├─ Contains: product_id, quantity
└─ Count: ~2.1M events

product_detail_recommendation_visible
├─ Source: Recommendation impression
├─ Contains: recommended_product_id
└─ Count: ~1.5M events

product_detail_recommendation_noticed
├─ Source: Recommendation engagement
├─ Contains: recommended_product_id
└─ Count: ~1.1M events

product_view_all_recommend_clicked
├─ Source: Recommendation click (category page)
├─ Contains: product_id from URL
└─ Count: ~0.8M events
```

### IP to Product Mapping

Each event links:
- IP Address → Geolocation (via ip_locations collection)
- IP Address → Product (via product_id in event)
- Product → Multiple Events (events are stored by type)

---

## Field Definitions

### Common Field Types

**Timestamp Fields**:
- Format: Unix timestamp (seconds since January 1, 1970)
- Example: `1591256275` = June 4, 2020, 10:04:35 UTC
- Conversion: `datetime.fromtimestamp(timestamp)`

**URL Fields**:
- Format: HTTP/HTTPS URL with possible query parameters
- May include: alloy type, stone type, campaign tracking
- Example: `https://www.glamira.ro/glamira-ring-orva.html?alloy=white-585&diamond=diamond-sapphire`

**Product ID Fields**:
- Format: Numeric string (7 digits)
- Range: 100000 to 99999 (actually 0 to 99999 in full system)
- Uniqueness: Each ID represents one SKU

**Country Codes**:
- Format: 2-letter ISO 3166-1 alpha-2
- Examples: `RO` (Romania), `US` (United States), `DE` (Germany)
- Reference: https://en.wikipedia.org/wiki/ISO_3166-1

**Coordinates**:
- Latitude: -90 (South Pole) to +90 (North Pole)
- Longitude: -180 (West) to +180 (East)
- Precision: 4-6 decimal places = 10-100 meters accuracy

---

## Data Quality Standards

### Validation Rules

**Product Data**:
- ✓ product_id must be non-empty
- ✓ product_name should contain at least 2 characters
- ✓ url must start with http:// or https://
- ✓ event_type must be one of the 7 defined types
- ✓ timestamp must be valid Unix timestamp (1970-2100)

**IP Location Data**:
- ✓ ip must be valid IPv4 format
- ✓ country must be 2-letter code
- ✓ latitude must be between -90 and 90
- ✓ longitude must be between -180 and 180
- ✓ count must be positive integer

**Encoding**:
- All text fields are UTF-8 encoded
- JSON files include BOM where necessary
- CSV files are comma-separated

### Data Completeness

**Products CSV**:
- 99.1% of products have valid names
- 0.9% have fallback numeric IDs (product_id as name)
- 100% have valid product_id
- 100% have URLs

**IP Locations**:
- 100% have valid IP addresses
- 99.8% have country information
- 95%+ have city-level data
- 85%+ have latitude/longitude

---

## Indexing Strategy

### Recommended MongoDB Indexes

```javascript
// For fast lookups
db.ip_locations.createIndex({ "ip": 1 })
db.ip_locations.createIndex({ "country": 1 })

// For aggregations
db.summary.createIndex({ "product_id": 1 })
db.summary.createIndex({ "collection": 1 })
db.summary.createIndex({ "time_stamp": 1 })

// Compound indexes
db.summary.createIndex({ "product_id": 1, "time_stamp": -1 })
```

---

## Data Export & Import

### Export from MongoDB

```bash
# Export collections to JSON
mongoexport --db countly --collection ip_locations --out ip_locations.json
mongoexport --db countly --collection summary --out summary.json

# Export with query
mongoexport --db countly --collection summary --query '{"collection":"view_product_detail"}' --out product_views.json
```

### Import to MongoDB

```bash
# Import from JSON
mongoimport --db countly --collection ip_locations --file ip_locations.json

# Import with mode
mongoimport --db countly --collection ip_locations --file ip_locations.json --mode upsert
```

---

## Schema Evolution

When adding new fields to existing collections:

1. **Backward Compatibility**: Code must handle missing fields
2. **Default Values**: Define defaults for null/missing values
3. **Migration**: Use MongoDB aggregation pipeline for batch updates
4. **Validation**: Update data quality checks
5. **Documentation**: Update this file with new fields

---

## References

- [MongoDB Documentation](https://docs.mongodb.com/)
- [ISO 3166-1 Country Codes](https://en.wikipedia.org/wiki/ISO_3166-1)
- [Unix Timestamp Reference](https://www.epochconverter.com/)
- [GeoJSON Specification](https://tools.ietf.org/html/rfc7946)

For more information, see [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) and README.md.
