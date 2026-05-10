#This file was created for the finding schema purpose

# preparation: get the data from mongodb database (summary collection) -> export them to JSONL format and place it to the project folder 
# next: use python script, parse jsonl file to find the full fields of the schema (the jsonl file is 41 million record and 34GB data)
# - make sure you can extract all the format, the fileds that are nested, and more over, not out of memory
# => ready for import to bigquery

import json
import os
from collections import defaultdict
from pathlib import Path


class SchemaExtractor:
    """Extract schema from JSONL file without loading entire file into memory."""
    
    def __init__(self, jsonl_path, output_dir="output"):
        self.jsonl_path = jsonl_path
        self.output_dir = output_dir
        self.field_types = defaultdict(set)  # Track all types for each field
        self.field_type_counts = defaultdict(lambda: defaultdict(int))  # Count occurrences of each type
        self.field_examples = defaultdict(list)  # Store examples for each field
        self.array_examples = defaultdict(list)  # Store sample array items
        self.field_nullability = defaultdict(lambda: {"null": 0, "non_null": 0})
        self.array_item_types = defaultdict(set)  # Track types in arrays
        self.array_field_counts = defaultdict(lambda: defaultdict(int))  # Count array item types
        self.mixed_type_fields = defaultdict(list)  # Track fields with multiple types
        self.lines_processed = 0
        self.errors = 0
        
    def get_nested_path(self, obj, prefix=""):
        """Recursively extract all field paths and their types."""
        if obj is None:
            return {f"{prefix}": "null"} if prefix else {}
        
        result = {}
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                path = f"{prefix}.{key}" if prefix else key
                
                if value is None:
                    result[path] = "null"
                elif isinstance(value, dict):
                    # Handle special MongoDB types like $oid
                    if "$oid" in value:
                        result[path] = "string"  # $oid is a string representation
                    else:
                        # Recursively process nested objects
                        nested = self.get_nested_path(value, path)
                        result.update(nested)
                elif isinstance(value, list):
                    if len(value) > 0:
                        first_item = value[0]
                        if isinstance(first_item, dict):
                            result[f"{path}"] = "array_of_objects"
                            # Process first item to get structure
                            nested = self.get_nested_path(first_item, path)
                            result.update(nested)
                        elif isinstance(first_item, list):
                            result[path] = "array_of_arrays"
                        else:
                            result[path] = f"array_of_{type(first_item).__name__}"
                    else:
                        result[path] = "array"
                elif isinstance(value, bool):
                    result[path] = "boolean"
                elif isinstance(value, int):
                    result[path] = "integer"
                elif isinstance(value, float):
                    result[path] = "float"
                elif isinstance(value, str):
                    result[path] = "string"
                else:
                    result[path] = type(value).__name__
        
        return result
    
    def process_line(self, line):
        """Process a single JSON line."""
        try:
            record = json.loads(line)
            paths = self.get_nested_path(record)
            
            # Extract array examples
            self._extract_array_samples(record)
            
            for path, data_type in paths.items():
                if data_type != "null":
                    self.field_types[path].add(data_type)
                    self.field_type_counts[path][data_type] += 1
                    self.field_nullability[path]["non_null"] += 1
                else:
                    self.field_nullability[path]["null"] += 1
            
            return True
        except json.JSONDecodeError as e:
            self.errors += 1
            return False
    
    def _extract_array_samples(self, obj, prefix="", max_examples=3):
        """Extract sample items from arrays for documentation."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                path = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, list) and len(value) > 0:
                    # Store samples of array items
                    if len(self.array_examples[path]) < max_examples:
                        for item in value[:1]:  # Get first item of the array
                            if item not in self.array_examples[path]:
                                self.array_examples[path].append(item)
                    
                    # Recursively process array items
                    for item in value:
                        if isinstance(item, dict):
                            self._extract_array_samples(item, path, max_examples)
                elif isinstance(value, dict):
                    self._extract_array_samples(value, path, max_examples)
    
    def extract_schema(self, sample_size=None):
        """Extract schema from JSONL file line by line."""
        print(f"Starting schema extraction from: {self.jsonl_path}")
        
        try:
            with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    if self.process_line(line):
                        self.lines_processed += 1
                    
                    # Progress indicator every 100,000 lines
                    if self.lines_processed % 100000 == 0:
                        print(f"Processed {self.lines_processed:,} lines...")
                    
                    # Optional: limit processing for testing
                    if sample_size and self.lines_processed >= sample_size:
                        break
        
        except FileNotFoundError:
            print(f"Error: File not found at {self.jsonl_path}")
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
        
        return True
    
    def generate_schema_report(self):
        """Generate and save schema report with type distribution."""
        os.makedirs(self.output_dir, exist_ok=True)
        
        report_path = os.path.join(self.output_dir, "schema_report.json")
        mixed_types_path = os.path.join(self.output_dir, "mixed_type_fields.json")
        
        schema = {}
        mixed_types_report = {}
        
        for field in sorted(self.field_types.keys()):
            types = self.field_types[field]
            type_counts = self.field_type_counts[field]
            nullability = self.field_nullability[field]
            total = nullability["null"] + nullability["non_null"]
            
            # Calculate type distribution percentages
            type_distribution = {}
            for dtype, count in sorted(type_counts.items()):
                percentage = round((count / nullability["non_null"] * 100), 2) if nullability["non_null"] > 0 else 0
                type_distribution[dtype] = {
                    "count": count,
                    "percentage": percentage
                }
            
            schema[field] = {
                "types": list(types),
                "type_distribution": type_distribution,
                "null_count": nullability["null"],
                "non_null_count": nullability["non_null"],
                "total_occurrences": total,
                "null_percentage": round((nullability["null"] / total * 100), 2) if total > 0 else 0,
                "has_mixed_types": len(types) > 1
            }
            
            # Track fields with multiple types
            if len(types) > 1:
                mixed_types_report[field] = type_distribution
        
        # Save main schema report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        # Save mixed types report
        with open(mixed_types_path, 'w', encoding='utf-8') as f:
            json.dump(mixed_types_report, f, indent=2, ensure_ascii=False)
        
        # Generate array structure report
        self._generate_array_structure_report()
        
        print(f"\nSchema report saved to: {report_path}")
        print(f"Mixed type fields saved to: {mixed_types_path}")
        return schema
    
    def _generate_array_structure_report(self):
        """Generate detailed report of array structures with examples."""
        array_report_path = os.path.join(self.output_dir, "array_structure_report.json")
        
        array_structures = {}
        
        # Identify array fields
        array_fields = [field for field in self.field_types.keys() 
                       if any('array' in t for t in self.field_types[field])]
        
        for field in sorted(array_fields):
            types = self.field_types[field]
            type_counts = self.field_type_counts[field]
            
            # Determine the structure
            structure_info = {
                "field_path": field,
                "array_types": list(types),
                "type_distribution": {}
            }
            
            for atype, count in sorted(type_counts.items()):
                percentage = round((count / self.lines_processed * 100), 2)
                structure_info["type_distribution"][atype] = {
                    "count": count,
                    "percentage": percentage
                }
            
            # Add sample items if available
            if field in self.array_examples and self.array_examples[field]:
                structure_info["sample_items"] = self.array_examples[field][:3]
            
            # Determine if this is an array of objects
            is_array_of_objects = any('array_of_objects' in t for t in types)
            structure_info["is_array_of_objects"] = is_array_of_objects
            
            # List all nested fields under this array
            nested_fields = [f for f in self.field_types.keys() 
                           if f.startswith(field + ".")]
            structure_info["nested_fields"] = nested_fields
            
            array_structures[field] = structure_info
        
        with open(array_report_path, 'w', encoding='utf-8') as f:
            json.dump(array_structures, f, indent=2, ensure_ascii=False)
        
        print(f"Array structure report saved to: {array_report_path}")
    
    def generate_bigquery_schema(self, schema_dict):
        """Convert extracted schema to BigQuery format."""
        bq_schema_path = os.path.join(self.output_dir, "bigquery_schema.json")
        
        def get_bigquery_type(field_name, types_set):
            """Map Python types to BigQuery types, handling mixed types."""
            types_set = set(types_set)
            
            # Single type mapping
            type_map = {
                "string": "STRING",
                "integer": "INTEGER",
                "float": "FLOAT64",
                "boolean": "BOOLEAN",
                "null": "STRING",
            }
            
            # Remove null from consideration for primary type
            if "null" in types_set:
                types_set_clean = types_set.copy()
                types_set_clean.discard("null")
            else:
                types_set_clean = types_set
            
            # If single type remains
            if len(types_set_clean) == 1:
                return type_map.get(list(types_set_clean)[0], "STRING")
            
            # Multiple types - use STRING for flexibility
            if len(types_set_clean) > 1:
                print(f"  Field '{field_name}' has mixed types {types_set_clean} -> Using STRING")
                return "STRING"
            
            # Only null
            return "STRING"
        
        def create_nested_schema(fields_dict):
            """Create nested BigQuery schema structure."""
            bq_fields = []
            processed = set()
            
            for field_path in sorted(fields_dict.keys()):
                if field_path in processed:
                    continue
                
                parts = field_path.split('.')
                parent_path = '.'.join(parts[:-1])
                
                # Skip if this is a sub-field of an array or nested object
                if any(parent_path.startswith(p.split('[')[0]) for p in processed):
                    continue
                
                field_name = parts[-1]
                types = fields_dict[field_path]["types"]
                
                # Check if this field has nested children
                nested_fields = [
                    p for p in fields_dict.keys()
                    if p.startswith(field_path + ".") and p != field_path
                ]
                
                if "array_of_objects" in types or nested_fields:
                    if nested_fields:
                        sub_fields = create_nested_schema({
                            p: fields_dict[p] for p in nested_fields
                            if p.startswith(field_path + ".")
                        })
                        bq_fields.append({
                            "name": field_name,
                            "type": "RECORD",
                            "mode": "REPEATED" if "array_of_objects" in types else "NULLABLE",
                            "fields": sub_fields
                        })
                    else:
                        bq_fields.append({
                            "name": field_name,
                            "type": "STRING",
                            "mode": "REPEATED"
                        })
                else:
                    bq_type = get_bigquery_type(field_path, types)
                    bq_fields.append({
                        "name": field_name,
                        "type": bq_type,
                        "mode": "NULLABLE"
                    })
                
                processed.add(field_path)
            
            return bq_fields
        
        print("\nGenerating BigQuery schema...")
        # Simplified BigQuery schema
        bq_schema = create_nested_schema(schema_dict)
        
        with open(bq_schema_path, 'w', encoding='utf-8') as f:
            json.dump(bq_schema, f, indent=2)
        
        print(f"BigQuery schema saved to: {bq_schema_path}")
        return bq_schema
    
    def print_summary(self):
        """Print extraction summary."""
        mixed_type_count = sum(1 for field in self.field_types.keys() if len(self.field_types[field]) > 1)
        array_field_count = sum(1 for field in self.field_types.keys() 
                               if any('array' in t for t in self.field_types[field]))
        
        print("\n" + "="*80)
        print("SCHEMA EXTRACTION SUMMARY")
        print("="*80)
        print(f"Lines processed: {self.lines_processed:,}")
        print(f"Errors encountered: {self.errors}")
        print(f"Total unique fields: {len(self.field_types)}")
        print(f"Array fields: {array_field_count}")
        print(f"Fields with mixed types: {mixed_type_count}")
        print("\n" + "-"*80)
        print("ARRAY FIELDS STRUCTURE")
        print("-"*80)
        
        # Show array fields with detailed info
        array_fields = sorted([f for f in self.field_types.keys() 
                             if any('array' in t for t in self.field_types[f])])
        
        for field in array_fields:
            types = self.field_types[field]
            type_counts = self.field_type_counts[field]
            
            if len(types) > 1:
                dist_str = ", ".join([f"{t}({type_counts[t]})" for t in sorted(types)])
                print(f"\n  {field}:")
                print(f"    Types: {dist_str} ⚠️ MIXED")
            else:
                atype = list(types)[0]
                print(f"\n  {field}:")
                print(f"    Type: {atype} (count: {type_counts[atype]})")
            
            # Show nested fields
            nested = [f for f in self.field_types.keys() if f.startswith(field + ".")]
            if nested:
                print(f"    Nested fields: {len(nested)}")
                for nf in nested[:5]:  # Show first 5
                    print(f"      - {nf.replace(field + '.', '')}: {', '.join(self.field_types[nf])}")
                if len(nested) > 5:
                    print(f"      ... and {len(nested) - 5} more")
        
        print("\n" + "-"*80)
        print("FIELDS WITH MIXED TYPES")
        print("-"*80)
        
        for field in sorted(self.field_types.keys()):
            types = self.field_types[field]
            type_counts = self.field_type_counts[field]
            
            if len(types) > 1:
                dist_str = ", ".join([
                    f"{t}({type_counts[t]})" for t in sorted(types)
                ])
                print(f"  - {field}: {dist_str}")


def main():
    """Main execution."""
    import sys
    
    # Configuration
    jsonl_file = "/home/tuancuong112504/prj5-gcp/summary.jsonl"
    output_dir = "/home/tuancuong112504/prj5-gcp/output"
    
    # Check if file exists
    if not os.path.exists(jsonl_file):
        print(f"Error: File not found at {jsonl_file}")
        print("Please ensure the JSONL file is exported from MongoDB first.")
        sys.exit(1)
    
    # Create extractor
    extractor = SchemaExtractor(jsonl_file, output_dir)
    
    # Extract schema
    if extractor.extract_schema():
        # Generate reports
        schema_dict = extractor.generate_schema_report()
        extractor.generate_bigquery_schema(schema_dict)
        extractor.print_summary()
        print("\n✓ Schema extraction completed successfully!")
    else:
        print("✗ Schema extraction failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

