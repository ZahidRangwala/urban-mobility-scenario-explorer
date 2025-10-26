from prefect import flow, task
import geopandas as gpd
import pandas as pd

@task
def fetch_osm_data(city_name: str):
    """Fetch street network data from OpenStreetMap."""
    import osmnx as ox
    print(f"Fetching OSM data for {city_name}...")
    graph = ox.graph_from_place(city_name, network_type="drive")
    gdf = ox.graph_to_gdfs(graph, nodes=False)
    return gdf

@task
def fetch_gtfs_data(gtfs_url: str):
    """Download GTFS data and load into a DataFrame."""
    import requests, zipfile, io, os
    os.makedirs("data/gtfs", exist_ok=True)
    print(f"Downloading GTFS data from {gtfs_url}...")
    r = requests.get(gtfs_url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("data/gtfs")
    routes = pd.read_csv("data/gtfs/routes.txt")
    return routes

@task
def process_data(osm_gdf: gpd.GeoDataFrame, routes: pd.DataFrame):
    """Join datasets, clean columns, and produce base travel segments."""
    print("Processing data...")
    osm_gdf = osm_gdf[['osmid', 'highway', 'geometry']]
    routes = routes[['route_id', 'route_long_name']]
    return osm_gdf.head(5), routes.head(5)

@flow(name="urban_mobility_pipeline")
def main_flow(city: str = "Chicago, Illinois", 
              gtfs_url: str = "https://transitfeeds.com/p/chicago-transit-authority/165/latest/download"):
    osm_data = fetch_osm_data(city)
    gtfs_data = fetch_gtfs_data(gtfs_url)
    clean_osm, clean_gtfs = process_data(osm_data, gtfs_data)
    print("Pipeline completed successfully.")
    return clean_osm, clean_gtfs

if __name__ == "__main__":
    main_flow()
