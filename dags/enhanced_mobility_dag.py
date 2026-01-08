from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Ensure src modules can be imported
sys.path.append('/opt/airflow')

# Import core logic (assuming dependencies are installed in the airflow image/env)
# In production, we'd package 'src' or use DockerOperator.
# For now, we rely on the volume mount mapping ./src -> /opt/airflow/src

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

def run_extract_osm(**kwargs):
    from src.enhanced_pipeline import extract_osm_data
    # In a real scenario, we'd use XCom to pass data paths, but here we'll assume shared volume
    # extract_osm_data in src currently returns a dataframe. 
    # Valid Airflow pattern: save DF to parquet on GCS/Local and pass path via XCom.
    df = extract_osm_data("Chicago, Illinois")
    
    # Save to temp location
    output_path = "/opt/airflow/data/osm_enhanced.parquet"
    df.to_parquet(output_path)
    return output_path

def run_extract_gtfs(**kwargs):
    from src.enhanced_pipeline import extract_gtfs_data
    df = extract_gtfs_data("https://www.transitchicago.com/downloads/sch_data/google_transit.zip")
    output_path = "/opt/airflow/data/gtfs_enhanced.parquet"
    df.to_parquet(output_path)
    return output_path

def run_extract_census(**kwargs):
    from src.enhanced_pipeline import extract_census_data
    df = extract_census_data("17")
    output_path = "/opt/airflow/data/census_enhanced.parquet"
    df.to_parquet(output_path)
    return output_path

def run_process_dask(**kwargs):
    import pandas as pd
    from src.enhanced_pipeline import process_with_dask
    
    # Load inputs
    ti = kwargs['ti']
    osm_path = ti.xcom_pull(task_ids='extract_osm')
    gtfs_path = ti.xcom_pull(task_ids='extract_gtfs')
    census_path = ti.xcom_pull(task_ids='extract_census')
    
    osm_df = pd.read_parquet(osm_path)
    gtfs_df = pd.read_parquet(gtfs_path)
    census_df = pd.read_parquet(census_path)
    
    # Execute processing
    osm_proc, transit_proc = process_with_dask(osm_df, gtfs_df, census_df)
    
    # Save outputs
    osm_proc.to_parquet("/opt/airflow/data/osm_processed.parquet")
    transit_proc.to_parquet("/opt/airflow/data/transit_processed.parquet")
    
    return ["/opt/airflow/data/osm_processed.parquet", "/opt/airflow/data/transit_processed.parquet"]

def run_create_unified(**kwargs):
    import pandas as pd
    from src.enhanced_pipeline import create_unified_dataset
    
    ti = kwargs['ti']
    census_path = ti.xcom_pull(task_ids='extract_census')
    
    osm_proc = pd.read_parquet("/opt/airflow/data/osm_processed.parquet")
    transit_proc = pd.read_parquet("/opt/airflow/data/transit_processed.parquet")
    census_df = pd.read_parquet(census_path)
    
    unified = create_unified_dataset(osm_proc, transit_proc, census_df)
    
    output_path = "/opt/airflow/data/unified_enhanced.parquet"
    unified.to_parquet(output_path)
    return output_path

def run_bq_load(**kwargs):
    import pandas as pd
    from src.enhanced_pipeline import store_in_bigquery
    
    ti = kwargs['ti']
    unified_path = ti.xcom_pull(task_ids='create_unified')
    
    df = pd.read_parquet(unified_path)
    store_in_bigquery(df, project_id="mystical-app-476502-m4")

with DAG(
    'enhanced_urban_mobility_pipeline',
    default_args=default_args,
    description='Enhanced Urban Mobility DAG with GCS/BigQuery',
    schedule_interval=None, # Manual trigger
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    t1 = PythonOperator(task_id='extract_osm', python_callable=run_extract_osm)
    t2 = PythonOperator(task_id='extract_gtfs', python_callable=run_extract_gtfs)
    t3 = PythonOperator(task_id='extract_census', python_callable=run_extract_census)
    
    t4 = PythonOperator(task_id='process_data', python_callable=run_process_dask)
    
    t5 = PythonOperator(task_id='create_unified', python_callable=run_create_unified)
    
    t6 = PythonOperator(task_id='load_bigquery', python_callable=run_bq_load)
    
    [t1, t2, t3] >> t4 >> t5 >> t6
