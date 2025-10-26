# Urban Mobility Scenario Explorer

A geospatial data engineering project inspired by Replica — exploring how city infrastructure changes affect mobility and accessibility.

## Features
- ETL pipeline with Prefect and Dask
- OSM + GTFS + Census integration
- Geospatial processing with GeoPandas and OSMnx
- Streamlit dashboard for scenario comparison
- Deployable via Docker / Kubernetes

## Quick Start

### Using the Start Script (Recommended)

The easiest way to get started is using the provided start script:

```bash
git clone https://github.com/yourusername/urban-mobility-scenario-explorer.git
cd urban-mobility-scenario-explorer
./start.sh
```

The script will:
- Detect if Docker is available and optionally use it
- Create a virtual environment if needed
- Install all dependencies
- Start the Streamlit dashboard on port 8501
- Start the Prefect server on port 4200

Then open your browser to:
- **Dashboard**: http://localhost:8501
- **Prefect UI**: http://localhost:4200

To stop all services:
```bash
./stop.sh
```

### Manual Setup

Alternatively, you can set up manually:

```bash
git clone https://github.com/yourusername/urban-mobility-scenario-explorer.git
cd urban-mobility-scenario-explorer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard/app.py
```
