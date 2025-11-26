#!/usr/bin/env python3
"""
Test script to verify BigQuery and GCS setup
"""

import os
import sys
from google.cloud import bigquery
from google.cloud import storage

def test_bigquery_connection(project_id: str):
    """Test BigQuery connection and list datasets"""
    print("🔍 Testing BigQuery connection...")
    
    try:
        client = bigquery.Client(project=project_id)
        
        # List datasets
        datasets = list(client.list_datasets())
        print(f"✅ BigQuery connection successful")
        print(f"Found {len(datasets)} datasets:")
        
        for dataset in datasets:
            print(f"  - {dataset.dataset_id}")
            
            # List tables in each dataset
            dataset_ref = client.dataset(dataset.dataset_id)
            tables = list(client.list_tables(dataset_ref))
            for table in tables:
                print(f"    └── {table.table_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ BigQuery connection failed: {e}")
        return False

def test_gcs_connection(project_id: str):
    """Test GCS connection and list buckets"""
    print("\n🔍 Testing Cloud Storage connection...")
    
    try:
        client = storage.Client(project=project_id)
        
        # List buckets
        buckets = list(client.list_buckets())
        print(f"✅ Cloud Storage connection successful")
        print(f"Found {len(buckets)} buckets:")
        
        for bucket in buckets:
            print(f"  - {bucket.name} (location: {bucket.location})")
        
        return True
        
    except Exception as e:
        print(f"❌ Cloud Storage connection failed: {e}")
        return False

def test_environment():
    """Test environment variables and dependencies"""
    print("🔍 Testing environment...")
    
    # Check environment variables
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if project_id:
        print(f"✅ GOOGLE_CLOUD_PROJECT: {project_id}")
    else:
        print("⚠️  GOOGLE_CLOUD_PROJECT not set")
    
    # Check credentials
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")
    else:
        print("ℹ️  Using default credentials (gcloud auth)")
    
    # Check required packages
    try:
        import pandas
        import geopandas
        import prefect
        print("✅ Required Python packages available")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_setup.py <PROJECT_ID>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    
    print("🚀 Testing Urban Mobility Pipeline Setup")
    print("=" * 50)
    
    # Test environment
    env_ok = test_environment()
    
    if env_ok:
        # Test BigQuery
        bq_ok = test_bigquery_connection(project_id)
        
        # Test GCS
        gcs_ok = test_gcs_connection(project_id)
        
        if bq_ok and gcs_ok:
            print("\n🎉 All tests passed! Your setup is ready.")
            print("\nNext steps:")
            print("1. Run: ./run_pipeline.sh")
            print("2. Select option 3 (Enhanced Pipeline)")
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
    else:
        print("\n❌ Environment setup incomplete. Please install missing packages.")
