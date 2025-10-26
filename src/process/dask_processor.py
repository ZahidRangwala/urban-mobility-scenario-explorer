"""
Dask Parallel Processing for Urban Mobility Data
Handles large-scale data processing with parallel computing
"""

import dask.dataframe as dd
import pandas as pd
import geopandas as gpd
from dask.distributed import Client, LocalCluster
from typing import Dict, List, Tuple, Optional
import numpy as np
from functools import partial

class DaskProcessor:
    def __init__(self, n_workers: int = 4, threads_per_worker: int = 2):
        self.n_workers = n_workers
        self.threads_per_worker = threads_per_worker
        self.client = None
        
    def start_cluster(self):
        """Start Dask cluster"""
        cluster = LocalCluster(
            n_workers=self.n_workers,
            threads_per_worker=self.threads_per_worker,
            memory_limit='2GB'
        )
        self.client = Client(cluster)
        print(f"Started Dask cluster with {self.n_workers} workers")
        return self.client
    
    def close_cluster(self):
        """Close Dask cluster"""
        if self.client:
            self.client.close()
            print("Closed Dask cluster")
    
    def process_segments_parallel(self, segments_df: pd.DataFrame, 
                                 chunk_size: int = 10000) -> dd.DataFrame:
        """Process segments in parallel using Dask"""
        if self.client is None:
            self.start_cluster()
        
        # Convert to Dask DataFrame
        ddf = dd.from_pandas(segments_df, npartitions=max(1, len(segments_df) // chunk_size))
        
        # Apply transformations in parallel
        ddf = ddf.map_partitions(self._process_segment_chunk, meta=segments_df.dtypes)
        
        return ddf
    
    def _process_segment_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Process a chunk of segments"""
        # Add derived features
        chunk = self._add_derived_features(chunk)
        
        # Calculate accessibility metrics
        chunk = self._calculate_accessibility_metrics(chunk)
        
        # Add performance indicators
        chunk = self._add_performance_indicators(chunk)
        
        return chunk
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features to segments"""
        # Speed efficiency
        if 'time_drive_min' in df.columns and 'length_m' in df.columns:
            df['speed_efficiency'] = df['length_m'] / (df['time_drive_min'] * 60)  # m/s
        
        # Accessibility score
        if 'is_walkable' in df.columns and 'is_cyclable' in df.columns and 'is_drivable' in df.columns:
            df['accessibility_score'] = (
                df['is_walkable'].astype(int) + 
                df['is_cyclable'].astype(int) + 
                df['is_drivable'].astype(int)
            ) / 3
        
        # Mode diversity
        if 'mode' in df.columns:
            df['mode_diversity'] = df['mode'].apply(self._calculate_mode_diversity)
        
        return df
    
    def _calculate_mode_diversity(self, mode: str) -> float:
        """Calculate mode diversity score"""
        mode_scores = {
            'mixed': 1.0,
            'car': 0.3,
            'bike': 0.7,
            'walk': 0.8,
            'transit': 0.9,
            'unknown': 0.1
        }
        return mode_scores.get(mode, 0.5)
    
    def _calculate_accessibility_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate accessibility metrics"""
        # Multi-modal accessibility
        if all(col in df.columns for col in ['is_walkable', 'is_cyclable', 'is_drivable']):
            df['multimodal_score'] = (
                df['is_walkable'].astype(int) * 0.4 +
                df['is_cyclable'].astype(int) * 0.3 +
                df['is_drivable'].astype(int) * 0.3
            )
        
        # Connectivity score (simplified)
        if 'length_m' in df.columns:
            df['connectivity_score'] = np.where(
                df['length_m'] < 500, 1.0,  # High connectivity for short segments
                np.where(df['length_m'] < 1000, 0.7, 0.4)  # Medium for medium, low for long
            )
        
        return df
    
    def _add_performance_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add performance indicators"""
        # Efficiency indicators
        if 'time_drive_min' in df.columns and 'time_walk_min' in df.columns:
            df['walk_drive_ratio'] = df['time_walk_min'] / df['time_drive_min']
        
        if 'time_bike_min' in df.columns and 'time_drive_min' in df.columns:
            df['bike_drive_ratio'] = df['time_bike_min'] / df['time_drive_min']
        
        # Sustainability score
        if all(col in df.columns for col in ['walk_drive_ratio', 'bike_drive_ratio']):
            df['sustainability_score'] = (
                (1 / df['walk_drive_ratio'].clip(0.1, 10)) * 0.4 +
                (1 / df['bike_drive_ratio'].clip(0.1, 10)) * 0.6
            )
        
        return df
    
    def aggregate_by_neighborhood(self, ddf: dd.DataFrame) -> pd.DataFrame:
        """Aggregate segments by neighborhood"""
        # Group by neighborhood and calculate aggregates
        neighborhood_stats = ddf.groupby('neighborhood').agg({
            'segment_id': 'count',
            'length_m': ['mean', 'sum'],
            'time_drive_min': 'mean',
            'time_walk_min': 'mean', 
            'time_bike_min': 'mean',
            'accessibility_score': 'mean',
            'multimodal_score': 'mean',
            'sustainability_score': 'mean',
            'population': 'first',
            'median_income': 'first'
        }).compute()
        
        # Flatten column names
        neighborhood_stats.columns = ['_'.join(col).strip() for col in neighborhood_stats.columns]
        
        return neighborhood_stats.reset_index()
    
    def calculate_mobility_metrics(self, ddf: dd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive mobility metrics"""
        # Calculate metrics in parallel
        metrics = ddf.groupby(['neighborhood', 'mode']).agg({
            'segment_id': 'count',
            'length_m': ['mean', 'sum'],
            'time_drive_min': 'mean',
            'time_walk_min': 'mean',
            'time_bike_min': 'mean',
            'accessibility_score': 'mean',
            'sustainability_score': 'mean'
        }).compute()
        
        # Flatten and clean column names
        metrics.columns = ['_'.join(col).strip() for col in metrics.columns]
        metrics = metrics.reset_index()
        
        return metrics


