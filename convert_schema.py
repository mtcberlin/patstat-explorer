#!/usr/bin/env python3
"""Convert EPO JSON schema to bq load format."""

import json
import sys

def convert_schema_to_bq(schema_file):
    """Convert JSON schema to bq load format (field:type,field:type,...)"""
    with open(schema_file, 'r') as f:
        schema = json.load(f)

    fields = []
    for col in schema['columns']:
        name = col['column_name']
        dtype = col['data_type']
        fields.append(f"{name}:{dtype}")

    return ','.join(fields)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: convert_schema.py <schema.json>")
        sys.exit(1)

    schema_file = sys.argv[1]
    print(convert_schema_to_bq(schema_file))
