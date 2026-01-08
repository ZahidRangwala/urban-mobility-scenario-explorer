"""
Simplified Urban Mobility ETL Pipeline
Focuses on core functionality with sample data
"""

# from prefect import flow, task # Removed for Airflow
import pandas as pd
import numpy as np
from datetime import datetime
import os

# @task # Removed
def create_sample_osm_data() -> pd.DataFrame:
    """Create sample OSM street segments"""
    print("Creating sample OSM data...")
    
    # Sample street segments for Chicago
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
    
    df = pd.DataFrame(osm_data)
    print(f"Created {len(df)} sample OSM segments")
    return df

# @task # Removed
def create_sample_transit_data() -> pd.DataFrame:
    """Create sample transit segments"""
    print("Creating sample transit data...")
    
    # Sample transit segments
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
    
    df = pd.DataFrame(transit_data)
    print(f"Created {len(df)} sample transit segments")
    return df

# @task # Removed
def create_sample_demographics() -> pd.DataFrame:
    """Create sample demographic data"""
    print("Creating sample demographics...")
    
    # Sample neighborhood demographics
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
    print(f"Created demographics for {len(df)} segments")
    return df

# @task # Removed
def create_unified_dataset(osm_df: pd.DataFrame, 
                          transit_df: pd.DataFrame,
                          demo_df: pd.DataFrame) -> pd.DataFrame:
    """Create unified dataset combining all sources"""
    print("Creating unified dataset...")
    
    # Standardize OSM data
    osm_standardized = pd.DataFrame({
        'segment_id': osm_df['segment_id'],
        'from': osm_df['from_node'],
        'to': osm_df['to_node'],
        'mode': osm_df['mode'],
        'time_min': osm_df['time_drive_min'],  # Use drive time as default
        'data_source': osm_df['data_source']
    })
    
    # Standardize transit data
    transit_standardized = pd.DataFrame({
        'segment_id': transit_df['segment_id'],
        'from': transit_df['from_stop_id'],
        'to': transit_df['to_stop_id'],
        'mode': transit_df['mode'],
        'time_min': transit_df['time_min'],
        'data_source': transit_df['data_source']
    })
    
    # Combine all segments
    all_segments = pd.concat([osm_standardized, transit_standardized], ignore_index=True)
    
    # Add demographics (simplified assignment)
    all_segments['neighborhood'] = np.random.choice(['Loop', 'Near North Side', 'Lincoln Park', 'Lakeview', 'Wicker Park'], len(all_segments))
    all_segments['population'] = np.random.randint(2000, 5000, len(all_segments))
    all_segments['median_income'] = np.random.randint(30000, 80000, len(all_segments))
    
    # Add derived metrics
    all_segments['accessibility_score'] = np.random.uniform(0.3, 1.0, len(all_segments))
    all_segments['equity_score'] = np.random.uniform(0.4, 1.0, len(all_segments))
    all_segments['efficiency_score'] = np.random.uniform(0.5, 1.0, len(all_segments))
    all_segments['created_at'] = datetime.now()
    
    print(f"Created unified dataset with {len(all_segments)} segments")
    print(f"Modes: {all_segments['mode'].value_counts().to_dict()}")
    print(f"Neighborhoods: {all_segments['neighborhood'].value_counts().to_dict()}")
    
    return all_segments

# @task # Removed
def export_results(unified_df: pd.DataFrame, 
                  output_dir: str = "data/output") -> dict:
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
        f.write(f"Data Sources: {unified_df['data_source'].value_counts().to_dict()}\n")
        f.write(f"Modes: {unified_df['mode'].value_counts().to_dict()}\n")
        f.write(f"Neighborhoods: {unified_df['neighborhood'].value_counts().to_dict()}\n")
        f.write(f"Average Travel Time: {unified_df['time_min'].mean():.2f} minutes\n")
        f.write(f"Average Population: {unified_df['population'].mean():.0f}\n")
        f.write(f"Average Median Income: ${unified_df['median_income'].mean():.0f}\n")
        f.write(f"Average Accessibility Score: {unified_df['accessibility_score'].mean():.2f}\n")
        f.write(f"Average Equity Score: {unified_df['equity_score'].mean():.2f}\n")
        f.write(f"Average Efficiency Score: {unified_df['efficiency_score'].mean():.2f}\n")
    
    print(f"Exported results to {output_dir}")
    return {
        'csv': csv_path,
        'parquet': parquet_path,
        'summary': summary_path
    }

# @flow(name="simple_urban_mobility_pipeline") # Removed
def simple_main_flow():
    """Simplified urban mobility ETL pipeline"""
    
    print("🚀 Starting Simplified Urban Mobility ETL Pipeline")
    print("=" * 60)
    
    # Create sample data
    osm_segments = create_sample_osm_data()
    transit_segments = create_sample_transit_data()
    demographics = create_sample_demographics()
    
    # Create unified dataset
    unified_df = create_unified_dataset(osm_segments, transit_segments, demographics)
    
    # Export results
    export_paths = export_results(unified_df)
    
    print("\n✅ Pipeline completed successfully!")
    print(f"📊 Dataset contains {len(unified_df)} segments")
    print(f"📁 Results exported to: {export_paths}")
    
    return unified_df, export_paths

if __name__ == "__main__":
    # Run the simplified pipeline
    result_df, paths = simple_main_flow()
    
    print(f"\n🎉 Pipeline completed! Check the results in: {paths}")
