"""
Enhanced Urban Mobility ETL Pipeline
Comprehensive data processing with OSM, GTFS, Census, and BigQuery integration
"""

# from prefect import flow, task # Removed for Airflow migration
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Tuple
import os
from datetime import datetime

# Import our custom modules
from ingest.osm_extractor import OSMExtractor
from ingest.gtfs_extractor import GTFSExtractor
from ingest.census_extractor import CensusExtractor
from process.dask_processor import DaskProcessor
from process.unified_dataset import UnifiedDatasetCreator
from utils.bigquery_client import BigQueryClient

# @task # Removed for Airflow migration
def extract_osm_data(city_name: str) -> pd.DataFrame:
    """Extract OSM street network data with detailed segments"""
    print(f"Extracting OSM data for {city_name}...")
    
    extractor = OSMExtractor(city_name)
    extractor.fetch_network()
    segments = extractor.get_segments_for_analysis()
    
    print(f"Extracted {len(segments)} OSM segments")
    return segments

# @task # Removed
def extract_gtfs_data(gtfs_url: str) -> pd.DataFrame:
    """Extract GTFS transit data"""
    print(f"Extracting GTFS data from {gtfs_url}...")
    
    extractor = GTFSExtractor(gtfs_url)
    extractor.download_and_extract()
    extractor.load_gtfs_tables()
    segments = extractor.create_transit_segments()
    
    print(f"Extracted {len(segments)} transit segments")
    return segments

# @task # Removed
def extract_census_data(state_fips: str = "17") -> pd.DataFrame:
    """Extract Census demographic data"""
    print("Extracting Census demographic data...")
    
    extractor = CensusExtractor()
    demographics = extractor.get_tract_demographics(state_fips)
    
    print(f"Extracted demographics for {len(demographics)} census tracts")
    return demographics

# @task # Removed
def process_with_dask(osm_segments: pd.DataFrame, 
                     transit_segments: pd.DataFrame,
                     demographics: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Process data using Dask for parallel computing"""
    print("Processing data with Dask...")
    
    processor = DaskProcessor(n_workers=4)
    
    try:
        processor.start_cluster()
        
        # Process OSM segments in parallel
        osm_processed = processor.process_segments_parallel(osm_segments)
        osm_processed = osm_processed.compute()
        
        # Process transit segments in parallel  
        transit_processed = processor.process_segments_parallel(transit_segments)
        transit_processed = transit_processed.compute()
        
        print(f"Processed {len(osm_processed)} OSM segments and {len(transit_processed)} transit segments")
        
        return osm_processed, transit_processed
        
    finally:
        processor.close_cluster()

# @task # Removed
def create_unified_dataset(osm_segments: pd.DataFrame,
                          transit_segments: pd.DataFrame, 
                          demographics: pd.DataFrame) -> pd.DataFrame:
    """Create unified dataset combining all sources"""
    print("Creating unified dataset...")
    
    creator = UnifiedDatasetCreator()
    unified_df = creator.create_unified_dataset(
        osm_segments, transit_segments, demographics
    )
    
    # Get summary
    summary = creator.get_dataset_summary()
    print(f"Created unified dataset with {summary.get('total_segments', 0)} segments")
    print(f"Modes: {summary.get('modes', {})}")
    print(f"Neighborhoods: {list(summary.get('neighborhoods', {}).keys())}")
    
    return unified_df

# @task # Removed
def store_in_bigquery(unified_df: pd.DataFrame, 
                     project_id: str = None) -> bool:
    """Store unified dataset in BigQuery"""
    print("Storing data in BigQuery...")
    
    client = BigQueryClient(project_id=project_id)
    
    # Create dataset and tables
    client.create_dataset()
    client.create_segments_table()
    client.create_od_matrices_table()
    
    # Upload data
    success = client.upload_dataframe(unified_df)
    
    if success:
        print("Successfully stored data in BigQuery")
        
        # Get some analytics
        metrics = client.get_mobility_metrics()
        if not metrics.empty:
            print(f"Generated mobility metrics for {len(metrics)} neighborhood-mode combinations")
        
        neighborhood_summary = client.get_neighborhood_summary()
        if not neighborhood_summary.empty:
            print(f"Generated neighborhood summaries for {len(neighborhood_summary)} neighborhoods")
    
    return success

# @task # Removed
def export_results(unified_df: pd.DataFrame, 
                  output_dir: str = "data/output") -> Dict[str, str]:
    """Export results to various formats"""
    print("Exporting results...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Export to CSV
    csv_path = os.path.join(output_dir, f"unified_mobility_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    unified_df.to_csv(csv_path, index=False)
    
    # Export to Parquet
    parquet_path = os.path.join(output_dir, f"unified_mobility_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet")
    unified_df.to_parquet(parquet_path, index=False)
    
    # Create summary report
    summary_path = os.path.join(output_dir, f"mobility_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(summary_path, 'w') as f:
        f.write("Urban Mobility Dataset Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total Segments: {len(unified_df)}\n")
        f.write(f"Data Sources: {unified_df.get('data_source', {}).value_counts().to_dict()}\n")
        f.write(f"Modes: {unified_df['mode'].value_counts().to_dict()}\n")
        f.write(f"Neighborhoods: {unified_df['neighborhood'].value_counts().to_dict()}\n")
        f.write(f"Average Travel Time: {unified_df['time_min'].mean():.2f} minutes\n")
        f.write(f"Average Population: {unified_df['population'].mean():.0f}\n")
        f.write(f"Average Median Income: ${unified_df['median_income'].mean():.0f}\n")
    
    print(f"Exported results to {output_dir}")
    return {
        'csv': csv_path,
        'parquet': parquet_path,
        'summary': summary_path
    }

# @flow(name="enhanced_urban_mobility_pipeline") # Removed
def enhanced_main_flow(
    city: str = "Chicago, Illinois",
    gtfs_url: str = "https://www.transitchicago.com/downloads/sch_data/google_transit.zip",
    state_fips: str = "17",
    project_id: str = None,
    use_bigquery: bool = False
):
    """Enhanced urban mobility ETL pipeline"""
    
    print("🚀 Starting Enhanced Urban Mobility ETL Pipeline")
    print("=" * 60)
    
    # Extract data from all sources
    osm_segments = extract_osm_data(city)
    transit_segments = extract_gtfs_data(gtfs_url)
    demographics = extract_census_data(state_fips)
    
    # Process with Dask for parallel computing
    osm_processed, transit_processed = process_with_dask(
        osm_segments, transit_segments, demographics
    )
    
    # Create unified dataset
    unified_df = create_unified_dataset(
        osm_processed, transit_processed, demographics
    )
    
    # Store in BigQuery if requested
    if use_bigquery and project_id:
        store_in_bigquery(unified_df, project_id)
    
    # Export results
    export_paths = export_results(unified_df)
    
    print("\n✅ Pipeline completed successfully!")
    print(f"📊 Dataset contains {len(unified_df)} segments")
    print(f"📁 Results exported to: {export_paths}")
    
    return unified_df, export_paths

if __name__ == "__main__":
    # Run the enhanced pipeline
    result_df, paths = enhanced_main_flow(
        city="Chicago, Illinois",
        use_bigquery=True,  # Enable BigQuery integration
        project_id=os.getenv('GOOGLE_CLOUD_PROJECT')  # Use environment variable
    )
    
    print(f"\n🎉 Pipeline completed! Check the results in: {paths}")



