#!/usr/bin/env python3
"""
Cloud Storage Setup Script for Urban Mobility Scenario Explorer
Creates buckets for raw and processed data
"""

import os
from google.cloud import storage
from google.cloud.exceptions import Conflict
from datetime import datetime

def create_gcs_buckets(project_id: str, region: str = "us-central1"):
    """Create Cloud Storage buckets for raw and processed data"""
    
    # Initialize Cloud Storage client
    client = storage.Client(project=project_id)
    
    # Define bucket names (must be globally unique)
    timestamp = datetime.now().strftime("%Y%m%d")
    raw_bucket_name = f"{project_id}-urban-mobility-raw-{timestamp}"
    processed_bucket_name = f"{project_id}-urban-mobility-processed-{timestamp}"
    
    buckets_created = []
    
    # 1. Create Raw Data Bucket
    print(f"Creating raw data bucket: {raw_bucket_name}")
    try:
        raw_bucket = client.create_bucket(
            raw_bucket_name,
            location=region
        )
        
        # Set lifecycle rules for raw data (delete after 90 days)
        lifecycle_rules = [
            {
                "action": {"type": "Delete"},
                "condition": {"age": 90}
            }
        ]
        raw_bucket.lifecycle_rules = lifecycle_rules
        raw_bucket.patch()
        
        print(f"✅ Raw data bucket created: gs://{raw_bucket_name}")
        buckets_created.append(raw_bucket_name)
        
    except Conflict:
        print(f"⚠️  Raw data bucket {raw_bucket_name} already exists")
        buckets_created.append(raw_bucket_name)
    except Exception as e:
        print(f"❌ Error creating raw data bucket: {e}")
    
    # 2. Create Processed Data Bucket
    print(f"Creating processed data bucket: {processed_bucket_name}")
    try:
        processed_bucket = client.create_bucket(
            processed_bucket_name,
            location=region
        )
        
        # Set lifecycle rules for processed data (delete after 365 days)
        lifecycle_rules = [
            {
                "action": {"type": "Delete"},
                "condition": {"age": 365}
            }
        ]
        processed_bucket.lifecycle_rules = lifecycle_rules
        processed_bucket.patch()
        
        print(f"✅ Processed data bucket created: gs://{processed_bucket_name}")
        buckets_created.append(processed_bucket_name)
        
    except Conflict:
        print(f"⚠️  Processed data bucket {processed_bucket_name} already exists")
        buckets_created.append(processed_bucket_name)
    except Exception as e:
        print(f"❌ Error creating processed data bucket: {e}")
    
    # 3. Create folder structure in buckets
    print("Creating folder structure...")
    
    for bucket_name in buckets_created:
        try:
            bucket = client.bucket(bucket_name)
            
            # Create folder structure
            folders = [
                "osm/",
                "gtfs/",
                "census/",
                "processed/",
                "exports/",
                "temp/"
            ]
            
            for folder in folders:
                blob = bucket.blob(folder)
                blob.upload_from_string("", content_type="application/x-www-form-urlencoded")
                print(f"  Created folder: gs://{bucket_name}/{folder}")
                
        except Exception as e:
            print(f"Error creating folders in {bucket_name}: {e}")
    
    # 4. Create environment configuration
    env_config = f"""
# Cloud Storage Configuration
export GCS_RAW_BUCKET="{raw_bucket_name}"
export GCS_PROCESSED_BUCKET="{processed_bucket_name}"
export GCS_REGION="{region}"
"""
    
    with open(".env.gcs", "w") as f:
        f.write(env_config)
    
    print(f"\n🎉 Cloud Storage setup completed!")
    print(f"Raw data bucket: gs://{raw_bucket_name}")
    print(f"Processed data bucket: gs://{processed_bucket_name}")
    print(f"Configuration saved to: .env.gcs")
    
    return {
        "raw_bucket": raw_bucket_name,
        "processed_bucket": processed_bucket_name,
        "region": region
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python setup_gcs.py <PROJECT_ID> [REGION]")
        print("Example: python setup_gcs.py my-gcp-project-123 us-central1")
        sys.exit(1)
    
    project_id = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "us-central1"
    
    create_gcs_buckets(project_id, region)
