# Google Cloud Platform Setup Guide
## Urban Mobility Data Ingestion Pipeline

This guide walks you through setting up GCP services for the urban mobility data pipeline.

## Prerequisites
- Google Cloud account ([sign up here](https://cloud.google.com/free))
- Basic understanding of cloud services
- Command line access (bash/zsh)

---

## Week 2-3: Data Ingestion Pipeline Setup

### Step 1: Create a GCP Project (5 minutes)

1. **Go to GCP Console**: https://console.cloud.google.com/
2. **Create New Project**:
   - Click "Select a project" → "New Project"
   - Project name: `urban-mobility-explorer`
   - Project ID: `urban-mobility-explorer-YYYY` (add your year)
   - Click "Create"

3. **Set Default Project**:
```bash
# Install gcloud CLI if not installed
# macOS: brew install google-cloud-sdk
# Linux: https://cloud.google.com/sdk/docs/install

# Login to GCP
gcloud auth login

# Set your project
gcloud config set project urban-mobility-explorer-YYYY
```

### Step 2: Enable Required APIs (10 minutes)

Enable the APIs needed for the pipeline:

```bash
# Enable BigQuery API
gcloud services enable bigquery.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage-component.googleapis.com

# Enable Cloud Functions API (for future automation)
gcloud services enable cloudfunctions.googleapis.com

# Enable BigQuery Data Transfer Service (for scheduled jobs)
gcloud services enable bigquerydatatransfer.googleapis.com

# Verify enabled services
gcloud services list --enabled
```

### Step 3: Set Up Service Account (10 minutes)

Create a service account for the application:

```bash
# Create service account
gcloud iam service-accounts create urban-mobility-service \
    --display-name="Urban Mobility Service Account"

# Get the service account email
SA_EMAIL=$(gcloud iam service-accounts list \
    --filter="displayName:Urban Mobility Service Account" \
    --format='value(email)')

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding urban-mobility-explorer-YYYY \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding urban-mobility-explorer-YYYY \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/bigquery.jobUser"

# Grant Cloud Storage permissions (for data exports)
gcloud projects add-iam-policy-binding urban-mobility-explorer-YYYY \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin"
```

### Step 4: Create Authentication Key (5 minutes)

```bash
# Create and download key
gcloud iam service-accounts keys create ~/urban-mobility-key.json \
    --iam-account=$SA_EMAIL

# Set environment variable (add to your ~/.bashrc or ~/.zshrc)
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/urban-mobility-key.json"
export GOOGLE_CLOUD_PROJECT="urban-mobility-explorer-YYYY"

# Reload your shell config
source ~/.bashrc  # or source ~/.zshrc
```

### Step 5: Set Up BigQuery (15 minutes)

```bash
# Create BigQuery dataset
bq mk --dataset \
    --location=US \
    --description="Urban mobility data warehouse" \
    urban-mobility-explorer-YYYY:urban_mobility

# Create tables for data ingestion
bq mk --table \
    urban-mobility-explorer-YYYY:urban_mobility.segments \
    src/utils/bigquery_schema.json

# Create table for OD matrices
bq mk --table \
    urban-mobility-explorer-YYYY:urban_mobility.od_matrices \
    origin:STRING,destination:STRING,mode:STRING,trips:INTEGER,duration_min:FLOAT,date:DATE
```

### Step 6: Create Cloud Storage Bucket (5 minutes)

```bash
# Create bucket for raw data storage
gsutil mb -p urban-mobility-explorer-YYYY -c STANDARD -l us-central1 \
    gs://urban-mobility-raw-data/

# Create bucket for processed data
gsutil mb -p urban-mobility-explorer-YYYY -c STANDARD -l us-central1 \
    gs://urban-mobility-processed-data/

# Set lifecycle policy (optional: auto-delete after 90 days)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [{
      "action": {"type": "Delete"},
      "condition": {"age": 90}
    }]
  }
}
EOF
gsutil lifecycle set lifecycle.json gs://urban-mobility-raw-data/
```

### Step 7: Configure Local Environment (5 minutes)

Create a configuration file in your project:

```bash
# Create .env file
cat > .env << EOF
GOOGLE_CLOUD_PROJECT=urban-mobility-explorer-YYYY
GOOGLE_APPLICATION_CREDENTIALS=$HOME/urban-mobility-key.json
BIGQUERY_DATASET=urban_mobility
GCS_BUCKET_RAW=gs://urban-mobility-raw-data/
GCS_BUCKET_PROCESSED=gs://urban-mobility-processed-data/
EOF

# Add to .gitignore (if not already there)
echo ".env" >> .gitignore
echo "urban-mobility-key.json" >> .gitignore
```

### Step 8: Test the Setup (10 minutes)

Run a test pipeline:

```bash
# Activate virtual environment
source venv/bin/activate

# Install GCP dependencies
pip install google-cloud-bigquery google-cloud-storage

# Run the enhanced pipeline with BigQuery
python src/enhanced_pipeline.py
```

Verify in BigQuery Console:
```bash
# Open BigQuery console
open "https://console.cloud.google.com/bigquery?project=urban-mobility-explorer-YYYY"

# Run a test query
bq query --use_legacy_sql=false \
    "SELECT * FROM urban_mobility.segments LIMIT 10"
```

---

## Data Pipeline Architecture

```
┌─────────────────┐
│  OSM/GIS Data   │
│  GTFS Feeds     │
│  Census Data    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Ingestion │  ← Prefect ETL Pipeline
│  & Cleaning     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cloud Storage  │  ← Raw data backup
│  (Temporary)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Processing    │  ← Dask parallel processing
│   & Validation  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   BigQuery      │  ← Data warehouse
│   (Production)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Dashboard      │  ← Streamlit visualization
│  & Analytics    │
└─────────────────┘
```

---

## Automated Scheduling (Optional)

Set up Cloud Scheduler for automated pipeline runs:

```bash
# Create Cloud Function for scheduling
gcloud functions deploy urban_mobility_pipeline \
    --runtime python39 \
    --trigger-http \
    --entry-point run_pipeline \
    --service-account $SA_EMAIL

# Create Cloud Scheduler job (daily at 2 AM)
gcloud scheduler jobs create http urban-mobility-daily \
    --location=us-central1 \
    --schedule="0 2 * * *" \
    --uri="https://YOUR-REGION-PROJECT.cloudfunctions.net/urban_mobility_pipeline" \
    --http-method=POST
```

---

## Cost Estimation

**Free Tier Includes:**
- BigQuery: 10 GB storage, 1 TB queries/month
- Cloud Storage: 5 GB/month
- Cloud Functions: 2 million invocations/month

**Estimated Costs** (beyond free tier):
- BigQuery: ~$0.02/GB storage, $5/TB queries
- Cloud Storage: ~$0.023/GB/month
- **Total: <$50/month** for development

---

## Troubleshooting

**Common Issues:**

1. **Authentication Error**:
```bash
# Re-authenticate
gcloud auth application-default login
```

2. **Permission Denied**:
```bash
# Check service account permissions
gcloud projects get-iam-policy urban-mobility-explorer-YYYY
```

3. **BigQuery API Not Enabled**:
```bash
# Enable API
gcloud services enable bigquery.googleapis.com
```

---

## Next Steps

1. ✅ Set up GCP project and services
2. ✅ Configure authentication
3. ✅ Run test pipeline
4. 🔄 Schedule automated data ingestion
5. 🔄 Build OD matrices from processed data
6. 🔄 Set up monitoring and alerting

For more details, see [Google Cloud Documentation](https://cloud.google.com/docs).
