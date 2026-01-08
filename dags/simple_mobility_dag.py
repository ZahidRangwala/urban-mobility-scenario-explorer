from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def create_sample_osm_data(**kwargs):
    """Create sample OSM street segments"""
    print("Creating sample OSM data...")
    # Sample logic copied from simple_pipeline.py
    osm_data = {
        'segment_id': [f'osm_{i}' for i in range(1, 101)],
        'from_node': [f'node_{i}' for i in range(1, 101)],
        'to_node': [f'node_{i+1}' for i in range(1, 101)],
        'mode': np.random.choice(['car', 'walk', 'bike', 'mixed'], 100),
        'highway': np.random.choice(['primary', 'secondary', 'residential', 'tertiary'], 100),
        'length_m': np.random.uniform(100, 2000, 100),
        'time_drive_min': np.random.uniform(1, 10, 100),
        'time_walk_min': np.random.uniform(5, 30, 100),
        'time_bike_min': np.random.uniform(2, 15, 100),
        'is_walkable': np.random.choice([True, False], 100),
        'is_cyclable': np.random.choice([True, False], 100),
        'is_drivable': np.random.choice([True, False], 100),
        'data_source': 'osm'
    }
    
    # Add geometry for visualization (borrowed from previous successful implementation)
    start_lats = np.random.uniform(41.80, 42.00, 100)
    start_lons = np.random.uniform(-87.80, -87.60, 100)
    end_lats = start_lats + np.random.uniform(-0.01, 0.01, 100)
    end_lons = start_lons + np.random.uniform(-0.01, 0.01, 100)
    
    osm_data['geometry'] = [f'LINESTRING ({sl} {sla}, {el} {ela})' 
                           for sl, sla, el, ela in zip(start_lons, start_lats, end_lons, end_lats)]

    df = pd.DataFrame(osm_data)
    # Save to XCom or file. For simplicity in this demo, saving to temp file to be picked up.
    # Ideally use XCom backend or external storage.
    output_path = "/opt/airflow/data/temp_osm.parquet"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path)
    return output_path

def create_sample_transit_data(**kwargs):
    print("Creating sample transit data...")
    transit_data = {
        'segment_id': [f'transit_{i}' for i in range(1, 51)],
        'from_stop_id': [f'stop_{i}' for i in range(1, 51)],
        'to_stop_id': [f'stop_{i+1}' for i in range(1, 51)],
        'route_id': [f'route_{i//5 + 1}' for i in range(1, 51)],
        'route_name': [f'Route {i//5 + 1}' for i in range(1, 51)],
        'mode': 'transit',
        'time_min': np.random.uniform(2, 20, 50),
        'distance_m': np.random.uniform(500, 5000, 50),
        'data_source': 'transit'
    }
    
    # Add geometry
    start_lats = np.random.uniform(41.80, 42.00, 50)
    start_lons = np.random.uniform(-87.80, -87.60, 50)
    end_lats = start_lats + np.random.uniform(-0.01, 0.01, 50)
    end_lons = start_lons + np.random.uniform(-0.01, 0.01, 50)
    
    transit_data['geometry'] = [f'LINESTRING ({sl} {sla}, {el} {ela})' 
                               for sl, sla, el, ela in zip(start_lons, start_lats, end_lons, end_lats)]

    df = pd.DataFrame(transit_data)
    output_path = "/opt/airflow/data/temp_transit.parquet"
    df.to_parquet(output_path)
    return output_path

def create_sample_demographics(**kwargs):
    print("Creating sample demographics...")
    neighborhoods = ['Loop', 'Near North Side', 'Lincoln Park', 'Lakeview', 'Wicker Park']
    demo_data = {
        'neighborhood': np.random.choice(neighborhoods, 100),
        'population': np.random.randint(2000, 5000, 100),
        'median_income': np.random.randint(30000, 80000, 100),
        'transit_share': np.random.uniform(0.1, 0.4, 100),
        'walk_bike_share': np.random.uniform(0.05, 0.2, 100),
        'car_share': np.random.uniform(0.4, 0.8, 100)
    }
    df = pd.DataFrame(demo_data)
    output_path = "/opt/airflow/data/temp_demo.parquet"
    df.to_parquet(output_path)
    return output_path

def create_unified_dataset(**kwargs):
    print("Creating unified dataset...")
    # Load from previous steps
    osm_df = pd.read_parquet("/opt/airflow/data/temp_osm.parquet")
    transit_df = pd.read_parquet("/opt/airflow/data/temp_transit.parquet")
    # demo_df = pd.read_parquet("/opt/airflow/data/temp_demo.parquet") # Not used in join logic yet but loaded for completeness

    # Standardize OSM data
    osm_standardized = pd.DataFrame({
        'segment_id': osm_df['segment_id'],
        'from': osm_df['from_node'],
        'to': osm_df['to_node'],
        'mode': osm_df['mode'],
        'time_min': osm_df['time_drive_min'],
        'data_source': osm_df['data_source'],
        'geometry': osm_df['geometry']
    })
    
    # Standardize transit data
    transit_standardized = pd.DataFrame({
        'segment_id': transit_df['segment_id'],
        'from': transit_df['from_stop_id'],
        'to': transit_df['to_stop_id'],
        'mode': transit_df['mode'],
        'time_min': transit_df['time_min'],
        'data_source': transit_df['data_source'],
        'geometry': transit_df['geometry']
    })
    
    # Combine
    all_segments = pd.concat([osm_standardized, transit_standardized], ignore_index=True)
    
    # Add demographics
    all_segments['neighborhood'] = np.random.choice(['Loop', 'Near North Side', 'Lincoln Park', 'Lakeview', 'Wicker Park'], len(all_segments))
    all_segments['population'] = np.random.randint(2000, 5000, len(all_segments))
    all_segments['median_income'] = np.random.randint(30000, 80000, len(all_segments))
    
    # Metrics
    all_segments['accessibility_score'] = np.random.uniform(0.3, 1.0, len(all_segments))
    all_segments['equity_score'] = np.random.uniform(0.4, 1.0, len(all_segments))
    all_segments['efficiency_score'] = np.random.uniform(0.5, 1.0, len(all_segments))
    all_segments['created_at'] = datetime.now()
    
    # Export
    output_dir = "/opt/airflow/data/output"
    os.makedirs(output_dir, exist_ok=True)
    
    csv_path = os.path.join(output_dir, f"unified_mobility_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    all_segments.to_csv(csv_path, index=False)
    print(f"Exported to {csv_path}")

with DAG(
    'simple_urban_mobility_pipeline',
    default_args=default_args,
    description='Simplified Urban Mobility DAG',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    t1 = PythonOperator(
        task_id='create_sample_osm_data',
        python_callable=create_sample_osm_data,
    )

    t2 = PythonOperator(
        task_id='create_sample_transit_data',
        python_callable=create_sample_transit_data,
    )

    t3 = PythonOperator(
        task_id='create_sample_demographics',
        python_callable=create_sample_demographics,
    )

    t4 = PythonOperator(
        task_id='create_unified_dataset',
        python_callable=create_unified_dataset,
    )

    [t1, t2, t3] >> t4
