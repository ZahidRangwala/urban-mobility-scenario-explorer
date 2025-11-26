"""
BigQuery Integration for Urban Mobility Data
Handles data storage and retrieval from Google BigQuery
"""

import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from typing import Dict, List, Optional
import os
import json
from datetime import datetime

class BigQueryClient:
    def __init__(self, project_id: str = None, dataset_id: str = "urban_mobility", schema_file: str = None):
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.dataset_id = dataset_id
        self.schema_file = schema_file or "src/utils/bigquery_schema.json"
        self.client = None
        
        if self.project_id:
            self.client = bigquery.Client(project=self.project_id)
        else:
            print("Warning: No Google Cloud project ID provided. BigQuery operations will be simulated.")
    
    def load_schema_from_file(self) -> List[bigquery.SchemaField]:
        """Load schema from JSON file"""
        try:
            with open(self.schema_file, 'r') as f:
                schema_config = json.load(f)
            
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
            return schema
        except Exception as e:
            print(f"Error loading schema from file: {e}")
            return self._get_default_schema()
    
    def _get_default_schema(self) -> List[bigquery.SchemaField]:
        """Fallback default schema"""
        return [
            bigquery.SchemaField("segment_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("from_node", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("to_node", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("mode", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("time_min", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("neighborhood", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("population", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("median_income", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
        ]
    
    def create_dataset(self) -> bool:
        """Create the dataset if it doesn't exist"""
        if not self.client:
            print("BigQuery client not available - simulating dataset creation")
            return True
        
        try:
            dataset_ref = self.client.dataset(self.dataset_id)
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            
            # Create dataset if it doesn't exist
            try:
                self.client.get_dataset(dataset_ref)
                print(f"Dataset {self.dataset_id} already exists")
            except NotFound:
                dataset = self.client.create_dataset(dataset)
                print(f"Created dataset {self.dataset_id}")
            
            return True
        except Exception as e:
            print(f"Error creating dataset: {e}")
            return False
    
    def create_segments_table(self) -> bool:
        """Create the segments table with proper schema"""
        if not self.client:
            print("BigQuery client not available - simulating table creation")
            return True
        
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.segments"
            
            # Load schema from file
            schema = self.load_schema_from_file()
            
            table = bigquery.Table(table_id, schema=schema)
            
            # Create table if it doesn't exist
            try:
                self.client.get_table(table_id)
                print(f"Table {table_id} already exists")
            except NotFound:
                table = self.client.create_table(table)
                print(f"Created table {table_id}")
            
            return True
        except Exception as e:
            print(f"Error creating table: {e}")
            return False
    
    def create_od_matrices_table(self) -> bool:
        """Create the OD matrices table"""
        if not self.client:
            print("BigQuery client not available - simulating OD matrices table creation")
            return True
        
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.od_matrices"
            
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
            
            table = bigquery.Table(table_id, schema=od_schema)
            
            # Create table if it doesn't exist
            try:
                self.client.get_table(table_id)
                print(f"OD matrices table {table_id} already exists")
            except NotFound:
                table = self.client.create_table(table)
                print(f"Created OD matrices table {table_id}")
            
            return True
        except Exception as e:
            print(f"Error creating OD matrices table: {e}")
            return False
    
    def upload_dataframe(self, df: pd.DataFrame, table_name: str = "segments") -> bool:
        """Upload DataFrame to BigQuery"""
        if not self.client:
            print("BigQuery client not available - simulating data upload")
            print(f"Would upload {len(df)} rows to {table_name}")
            return True
        
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            
            # Configure job
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",  # Replace table contents
                create_disposition="CREATE_IF_NEEDED"
            )
            
            # Upload data
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for job to complete
            
            print(f"Uploaded {len(df)} rows to {table_id}")
            return True
        except Exception as e:
            print(f"Error uploading data: {e}")
            return False
    
    def query_segments(self, query: str) -> pd.DataFrame:
        """Query segments from BigQuery"""
        if not self.client:
            print("BigQuery client not available - returning empty DataFrame")
            return pd.DataFrame()
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return results.to_dataframe()
        except Exception as e:
            print(f"Error querying data: {e}")
            return pd.DataFrame()
    
    def get_mobility_metrics(self) -> pd.DataFrame:
        """Get aggregated mobility metrics"""
        query = f"""
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
        FROM `{self.project_id}.{self.dataset_id}.segments`
        GROUP BY neighborhood, mode
        ORDER BY neighborhood, mode
        """
        
        return self.query_segments(query)
    
    def get_neighborhood_summary(self) -> pd.DataFrame:
        """Get neighborhood-level summary"""
        query = f"""
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
        FROM `{self.project_id}.{self.dataset_id}.segments`
        GROUP BY neighborhood
        ORDER BY avg_accessibility DESC
        """
        
        return self.query_segments(query)
    
    def get_mode_analysis(self) -> pd.DataFrame:
        """Get mode-specific analysis"""
        query = f"""
        SELECT 
            mode,
            COUNT(*) as segment_count,
            AVG(time_min) as avg_time,
            AVG(accessibility_score) as avg_accessibility,
            AVG(equity_score) as avg_equity,
            AVG(efficiency_score) as avg_efficiency,
            COUNT(DISTINCT neighborhood) as neighborhood_count
        FROM `{self.project_id}.{self.dataset_id}.segments`
        GROUP BY mode
        ORDER BY segment_count DESC
        """
        
        return self.query_segments(query)
    
    def export_to_gcs(self, bucket_name: str, file_prefix: str = "mobility_data") -> bool:
        """Export data to Google Cloud Storage"""
        if not self.client:
            print("BigQuery client not available - simulating GCS export")
            return True
        
        try:
            from google.cloud import storage
            
            # Export to GCS
            destination_uri = f"gs://{bucket_name}/{file_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            dataset_ref = self.client.dataset(self.dataset_id)
            table_ref = dataset_ref.table("segments")
            
            job_config = bigquery.ExtractJobConfig()
            job_config.destination_format = bigquery.DestinationFormat.CSV
            
            extract_job = self.client.extract_table(
                table_ref, destination_uri, job_config=job_config
            )
            extract_job.result()
            
            print(f"Exported data to {destination_uri}")
            return True
        except Exception as e:
            print(f"Error exporting to GCS: {e}")
            return False
