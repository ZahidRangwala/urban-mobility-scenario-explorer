# Urban Mobility Scenario Explorer

A geospatial data engineering project inspired by Replica — exploring how city infrastructure changes affect mobility and accessibility.

## Features
- ETL pipeline with Prefect and Dask
- OSM + GTFS + Census integration
- Geospatial processing with GeoPandas and OSMnx
- Streamlit dashboard for scenario comparison
- Deployable via Docker / Kubernetes

## Quick Start
```bash
git clone https://github.com/yourusername/urban-mobility-scenario-explorer.git
cd urban-mobility-scenario-explorer
pip install -r requirements.txt
python src/pipeline.py
streamlit run dashboard/app.py
```
