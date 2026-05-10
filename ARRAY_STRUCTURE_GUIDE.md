# Array Structure Analysis - Glamira Data

## Overview
Based on the schema extraction from 41.4M records, here's a detailed breakdown of all array fields and their structures:

---

## 1. **cart_products** - Mixed Array Type ⚠️

### Type Distribution:
- **array_of_objects**: 364,982 occurrences (79.74%)
- **array** (empty): 92,714 occurrences (20.26%)

### Format:
```json
{
  "cart_products": [
    {
      "product_id": 103324,           // integer
      "amount": 1,                     // integer
      "price": "129.99",               // string
      "currency": "EUR",               // string
      "option": [                      // MIXED: array_of_objects or string (see below)
        {
          "option_id": 261151,
          "option_label": "diamond",
          "value_id": 2166253,
          "value_label": "Swarovsky Cristall"
        }
      ]
    }
  ]
}
```

### Nested Fields Under `cart_products`:
| Field | Type | Count | Occurrence % |
|-------|------|-------|--------------|
| product_id | integer | 364,982 | 100% |
| amount | integer | 114,619 | 25.01% |
| price | string | 26,079 | 5.68% |
| currency | string | 26,079 | 5.68% |
| option | array_of_objects / string | 364,982 | 100% |

---

## 2. **cart_products.option** - Mixed Type ⚠️

### Type Distribution:
- **array_of_objects**: 342,621 occurrences (93.87%)
- **string**: 22,361 occurrences (6.13%)

### Format (when array_of_objects):
```json
{
  "option": [
    {
      "option_id": 261151,              // integer
      "option_label": "diamond",        // string
      "value_id": 2166253,              // integer
      "value_label": "Swarovsky Cristall" // string
    },
    {
      "option_id": 261154,
      "option_label": "alloy",
      "value_id": 2166328,
      "value_label": "Weißgold 585"
    }
  ]
}
```

### Format (when string):
```json
{
  "option": "serialized_string_representation"
}
```

### Nested Fields Under `cart_products.option`:
| Field | Type | Count | Occurrence % |
|-------|------|-------|--------------|
| option_id | integer | 342,621 | 100% |
| option_label | string | 342,621 | 100% |
| value_id | integer | 342,621 | 100% |
| value_label | string | 342,621 | 100% |

---

## 3. **option** - Top-Level Array ✓

### Type: array_of_objects

### Format:
```json
{
  "option": [
    {
      "option_id": "261151",            // string (attribute key)
      "option_label": "diamond",        // string
      "value_id": "2166253",            // string
      "value_label": "Swarovsky Cristall", // string
      "Kollektion": "BRILLANT",         // optional: string
      "alloy": "Weißgold 585",          // optional: string
      "category id": "123",             // optional: string
      "diamond": "Very Good",           // optional: string
      "finish": "Polished",             // optional: string
      "kollektion_id": "456",           // optional: string
      "pearlcolor": "White",            // optional: string
      "price": "100.00",                // optional: string
      "quality": "VVS1",                // optional: string
      "quality_label": "Excellent",     // optional: string
      "shapediamond": "Round",          // optional: string
      "stone": "Diamond",               // optional: string
    }
  ]
}
```

### Nested Fields Under `option`:
| Field | Type |
|-------|------|
| Kollektion | string |
| alloy | string |
| category id | string |
| diamond | string |
| finish | string |
| kollektion_id | string |
| option_id | string |
| option_label | string |
| pearlcolor | string |
| price | string |
| quality | string |
| quality_label | string |
| shapediamond | string |
| stone | string |
| value_id | string |
| value_label | string |

---

## Summary Statistics

### Array Fields Count:
- **cart_products**: Occurs in ~457K records
- **cart_products.option**: Occurs in ~364K records (nested within cart_products)
- **option**: Top-level array field

### Key Observations:

1. **Mixed Types Issues**: 
   - `cart_products` can be empty array or array of objects
   - `cart_products.option` can be array of objects or string
   - This requires careful handling during data import to BigQuery

2. **Data Density**:
   - Not all records have cart data (only 457K out of 41.4M have cart_products)
   - Not all cart items have options
   - Optional fields within option objects suggest they vary by product type

3. **Nullable Handling**:
   - When importing to BigQuery, mixed types should default to STRING mode
   - Empty arrays should be handled as null/empty repeated fields

---

## BigQuery Schema Recommendation

### For cart_products:
```json
{
  "name": "cart_products",
  "type": "RECORD",
  "mode": "REPEATED",
  "fields": [
    {"name": "product_id", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "amount", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "price", "type": "STRING", "mode": "NULLABLE"},
    {"name": "currency", "type": "STRING", "mode": "NULLABLE"},
    {
      "name": "option",
      "type": "RECORD",
      "mode": "REPEATED",
      "fields": [
        {"name": "option_id", "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "option_label", "type": "STRING", "mode": "NULLABLE"},
        {"name": "value_id", "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "value_label", "type": "STRING", "mode": "NULLABLE"}
      ]
    }
  ]
}
```

### For option (top-level):
```json
{
  "name": "option",
  "type": "RECORD",
  "mode": "REPEATED",
  "fields": [
    {"name": "option_id", "type": "STRING", "mode": "NULLABLE"},
    {"name": "option_label", "type": "STRING", "mode": "NULLABLE"},
    {"name": "value_id", "type": "STRING", "mode": "NULLABLE"},
    {"name": "value_label", "type": "STRING", "mode": "NULLABLE"},
    {"name": "Kollektion", "type": "STRING", "mode": "NULLABLE"},
    {"name": "alloy", "type": "STRING", "mode": "NULLABLE"},
    {"name": "category_id", "type": "STRING", "mode": "NULLABLE"},
    {"name": "diamond", "type": "STRING", "mode": "NULLABLE"},
    {"name": "finish", "type": "STRING", "mode": "NULLABLE"},
    {"name": "kollektion_id", "type": "STRING", "mode": "NULLABLE"},
    {"name": "pearlcolor", "type": "STRING", "mode": "NULLABLE"},
    {"name": "price", "type": "STRING", "mode": "NULLABLE"},
    {"name": "quality", "type": "STRING", "mode": "NULLABLE"},
    {"name": "quality_label", "type": "STRING", "mode": "NULLABLE"},
    {"name": "shapediamond", "type": "STRING", "mode": "NULLABLE"},
    {"name": "stone", "type": "STRING", "mode": "NULLABLE"}
  ]
}
```

---

## Data Processing Considerations

### Issues to Handle:
1. **Empty Arrays**: 20% of cart_products are empty arrays
2. **Mixed String/Object Types**: 6% of option fields are strings instead of arrays
3. **Varying Nested Fields**: Top-level option has many optional fields that don't appear in all records
4. **Data Type Conversion**: May need type conversion for numeric fields stored as strings

### Recommendations:
- Use BigQuery's SAFE_CAST for type conversions
- Handle empty arrays explicitly during import
- Consider creating separate tables for different option types
- Document data quality issues for stakeholders
