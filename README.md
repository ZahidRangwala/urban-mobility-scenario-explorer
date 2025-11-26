# Urban Mobility Scenario Explorer

A geospatial data engineering project inspired by Replica — exploring how city infrastructure changes affect mobility and accessibility.

## Features
- ETL pipeline with Prefect and Dask
- OSM + GTFS + Census integration
- Geospatial processing with GeoPandas and OSMnx
- Streamlit dashboard for scenario comparison
- Google Cloud Platform integration (BigQuery, Cloud Storage)
- Deployable via Docker / Kubernetes

## GCP Setup

For production deployment with Google Cloud Platform, see **[GCP_SETUP.md](GCP_SETUP.md)** for step-by-step instructions to:
- Set up BigQuery data warehouse
- Configure Cloud Storage for data ingestion
- Enable automated pipeline scheduling
- Implement data preprocessing and OD matrix generation

## Quick Start

### 1. Start the Dashboard

Start the Streamlit dashboard using Docker Compose:

```bash
git clone https://github.com/ZahidRangwala/urban-mobility-scenario-explorer.git
cd urban-mobility-scenario-explorer
./start.sh
```

Then open your browser to: **http://localhost:8501**

**Service Management:**
```bash
./start.sh    # Start all services
./stop.sh     # Stop all services
./restart.sh  # Restart all services
docker-compose logs -f    # View logs
```

### 2. Run Data Pipelines

To process and load data, use the pipeline runner:

```bash
./run_pipeline.sh
```

**Available Pipeline Options:**
1. **Simple Pipeline** - Uses sample data (no external downloads, fastest)
2. **Basic Pipeline** - Real OSM + GTFS data from Chicago
3. **Enhanced Pipeline** - Full ETL with OSM + GTFS + Census + BigQuery

### Manual Setup (Alternative)

If you prefer to run without Docker:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run dashboard
streamlit run dashboard/app.py

# Run pipeline
python src/simple_pipeline.py  # or pipeline.py, enhanced_pipeline.py
```
