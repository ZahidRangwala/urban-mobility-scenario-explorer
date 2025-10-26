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
- Use Docker Compose (recommended) if available for production-ready service management
- Fall back to regular Docker or Python if needed
- Create a virtual environment if running in Python mode
- Install all dependencies automatically
- Start the Streamlit dashboard on port 8501

Then open your browser to:
- **Dashboard**: http://localhost:8501

**Available commands:**
```bash
./start.sh    # Start all services
./stop.sh     # Stop all services
./restart.sh  # Restart all services

# With Docker Compose (automatic):
docker-compose logs -f    # View logs
docker-compose restart    # Restart services
docker-compose down       # Stop and remove containers
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
