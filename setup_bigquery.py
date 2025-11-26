#!/usr/bin/env python3
"""
BigQuery Setup Script for Urban Mobility Scenario Explorer
Creates dataset and tables using the schema configuration
"""

import json
import os
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from typing import Dict, List

def load_schema(schema_file: str) -> List[Dict]:
    """Load schema from JSON file"""
    with open(schema_file, 'r') as f:
        return json.load(f)

def create_bigquery_infrastructure(project_id: str, dataset_id: str = "urban_mobility"):
    """Create BigQuery dataset and tables"""
    
    # Initialize BigQuery client
    client = bigquery.Client(project=project_id)
    
    # 1. Create Dataset
    print(f"Creating dataset: {dataset_id}")
    dataset_ref = client.dataset(dataset_id)
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"  # You can change this to your preferred region
    dataset.description = "Urban mobility data for scenario analysis"
    
    try:
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"✅ Dataset {dataset_id} created successfully")
    except Exception as e:
        print(f"Dataset creation result: {e}")
    
    # 2. Create Segments Table
    print("Creating segments table...")
    schema_file = "src/utils/bigquery_schema.json"
    schema_config = load_schema(schema_file)
    
    # Convert schema config to BigQuery schema
    schema = []
    for field in schema_config:
        schema.append(
            bigquery.SchemaField(
                name=field["name"],
                field_type=field["type"],
                mode=field["mode"],
                description=field.get("description", "")
            )
        )
    
    segments_table_id = f"{project_id}.{dataset_id}.segments"
    segments_table = bigquery.Table(segments_table_id, schema=schema)
    
    try:
        segments_table = client.create_table(segments_table, exists_ok=True)
        print(f"✅ Segments table created successfully")
    except Exception as e:
        print(f"Segments table creation result: {e}")
    
    # 3. Create OD Matrices Table
    print("Creating OD matrices table...")
    od_schema = [
        bigquery.SchemaField("origin_id", "STRING", mode="REQUIRED", description="Origin location ID"),
        bigquery.SchemaField("destination_id", "STRING", mode="REQUIRED", description="Destination location ID"),
        bigquery.SchemaField("origin_neighborhood", "STRING", mode="REQUIRED", description="Origin neighborhood"),
        bigquery.SchemaField("destination_neighborhood", "STRING", mode="REQUIRED", description="Destination neighborhood"),
        bigquery.SchemaField("mode", "STRING", mode="REQUIRED", description="Transportation mode"),
        bigquery.SchemaField("travel_time_min", "FLOAT", mode="REQUIRED", description="Travel time in minutes"),
        bigquery.SchemaField("distance_m", "FLOAT", mode="NULLABLE", description="Distance in meters"),
        bigquery.SchemaField("accessibility_score", "FLOAT", mode="NULLABLE", description="Accessibility score"),
        bigquery.SchemaField("equity_score", "FLOAT", mode="NULLABLE", description="Equity score"),
        bigquery.SchemaField("efficiency_score", "FLOAT", mode="NULLABLE", description="Efficiency score"),
        bigquery.SchemaField("population_origin", "INTEGER", mode="NULLABLE", description="Origin population"),
        bigquery.SchemaField("population_destination", "INTEGER", mode="NULLABLE", description="Destination population"),
        bigquery.SchemaField("median_income_origin", "FLOAT", mode="NULLABLE", description="Origin median income"),
        bigquery.SchemaField("median_income_destination", "FLOAT", mode="NULLABLE", description="Destination median income"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="Record creation timestamp")
    ]
    
    od_table_id = f"{project_id}.{dataset_id}.od_matrices"
    od_table = bigquery.Table(od_table_id, schema=od_schema)
    
    try:
        od_table = client.create_table(od_table, exists_ok=True)
        print(f"✅ OD matrices table created successfully")
    except Exception as e:
        print(f"OD matrices table creation result: {e}")
    
    # 4. Create Views for Analytics
    print("Creating analytics views...")
    
    # Mobility metrics view
    mobility_view_query = f"""
    CREATE OR REPLACE VIEW `{project_id}.{dataset_id}.mobility_metrics` AS
    SELECT 
        neighborhood,
        mode,
        COUNT(*) as segment_count,
        AVG(time_min) as avg_time_min,
        AVG(accessibility_score) as avg_accessibility,
        AVG(equity_score) as avg_equity,
        AVG(efficiency_score) as avg_efficiency,
        AVG(population) as avg_population,
        AVG(median_income) as avg_income
    FROM `{project_id}.{dataset_id}.segments`
    GROUP BY neighborhood, mode
    """
    
    try:
        client.query(mobility_view_query).result()
        print("✅ Mobility metrics view created")
    except Exception as e:
        print(f"Mobility metrics view creation result: {e}")
    
    # Neighborhood summary view
    neighborhood_view_query = f"""
    CREATE OR REPLACE VIEW `{project_id}.{dataset_id}.neighborhood_summary` AS
    SELECT 
        neighborhood,
        COUNT(*) as total_segments,
        COUNT(DISTINCT mode) as mode_diversity,
        AVG(time_min) as avg_travel_time,
        AVG(accessibility_score) as avg_accessibility,
        AVG(equity_score) as avg_equity,
        AVG(efficiency_score) as avg_efficiency,
        AVG(population) as population,
        AVG(median_income) as median_income
    FROM `{project_id}.{dataset_id}.segments`
    GROUP BY neighborhood
    ORDER BY avg_accessibility DESC
    """
    
    try:
        client.query(neighborhood_view_query).result()
        print("✅ Neighborhood summary view created")
    except Exception as e:
        print(f"Neighborhood summary view creation result: {e}")
    
    print(f"\n🎉 BigQuery setup completed!")
    print(f"Dataset: {project_id}.{dataset_id}")
    print(f"Tables: segments, od_matrices")
    print(f"Views: mobility_metrics, neighborhood_summary")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python setup_bigquery.py <PROJECT_ID>")
        print("Example: python setup_bigquery.py my-gcp-project-123")
        sys.exit(1)
    
    project_id = sys.argv[1]
    create_bigquery_infrastructure(project_id)
