"""
Unified Dataset Creator
Combines OSM, GTFS, and Census data into a comprehensive mobility dataset
"""

import pandas as pd
import geopandas as gpd
from typing import Dict, List, Tuple, Optional
import numpy as np
from datetime import datetime

class UnifiedDatasetCreator:
    def __init__(self):
        self.unified_df = None
        self.schema = {
            'segment_id': 'string',
            'from': 'string', 
            'to': 'string',
            'mode': 'string',
            'time_min': 'float',
            'neighborhood': 'string',
            'population': 'int',
            'median_income': 'float'
        }
    
    def create_unified_dataset(self, osm_segments: pd.DataFrame, 
                              transit_segments: pd.DataFrame,
                              demographics: pd.DataFrame) -> pd.DataFrame:
        """Create unified dataset from all sources"""
        
        # Standardize OSM segments
        osm_standardized = self._standardize_osm_segments(osm_segments)
        
        # Standardize transit segments  
        transit_standardized = self._standardize_transit_segments(transit_segments)
        
        # Combine all segments
        all_segments = pd.concat([osm_standardized, transit_standardized], ignore_index=True)
        
        # Add demographic data
        unified_df = self._add_demographics(all_segments, demographics)
        
        # Add derived metrics
        unified_df = self._add_derived_metrics(unified_df)
        
        # Ensure schema compliance
        unified_df = self._ensure_schema_compliance(unified_df)
        
        self.unified_df = unified_df
        return unified_df
    
    def _standardize_osm_segments(self, osm_df: pd.DataFrame) -> pd.DataFrame:
        """Standardize OSM segments to unified schema"""
        standardized = pd.DataFrame()
        
        # Map OSM columns to unified schema
        standardized['segment_id'] = osm_df.get('segment_id', '')
        standardized['from'] = osm_df.get('from_node', '')
        standardized['to'] = osm_df.get('to_node', '')
        standardized['mode'] = osm_df.get('mode', 'unknown')
        
        # Use appropriate time based on mode
        time_cols = ['time_drive_min', 'time_walk_min', 'time_bike_min']
        if 'mode' in osm_df.columns:
            standardized['time_min'] = osm_df.apply(
                lambda row: self._get_time_for_mode(row, time_cols), axis=1
            )
        else:
            standardized['time_min'] = osm_df.get('time_drive_min', 0)
        
        # Add geometry if available
        if 'geometry' in osm_df.columns:
            standardized['geometry'] = osm_df['geometry']
        
        # Add source identifier
        standardized['data_source'] = 'osm'
        
        return standardized
    
    def _standardize_transit_segments(self, transit_df: pd.DataFrame) -> pd.DataFrame:
        """Standardize transit segments to unified schema"""
        standardized = pd.DataFrame()
        
        # Map transit columns to unified schema
        standardized['segment_id'] = transit_df.get('segment_id', '')
        standardized['from'] = transit_df.get('from_stop_id', '')
        standardized['to'] = transit_df.get('to_stop_id', '')
        standardized['mode'] = 'transit'
        standardized['time_min'] = transit_df.get('time_min', 0)
        
        # Add geometry if available
        if 'geometry' in transit_df.columns:
            standardized['geometry'] = transit_df['geometry']
        
        # Add route information
        standardized['route_id'] = transit_df.get('route_id', '')
        standardized['route_name'] = transit_df.get('route_name', '')
        
        # Add source identifier
        standardized['data_source'] = 'transit'
        
        return standardized
    
    def _get_time_for_mode(self, row: pd.Series, time_cols: List[str]) -> float:
        """Get appropriate time based on mode"""
        mode = row.get('mode', 'unknown')
        
        if mode == 'car' and 'time_drive_min' in row:
            return row['time_drive_min']
        elif mode == 'walk' and 'time_walk_min' in row:
            return row['time_walk_min']
        elif mode == 'bike' and 'time_bike_min' in row:
            return row['time_bike_min']
        else:
            # Return first available time
            for col in time_cols:
                if col in row and pd.notna(row[col]):
                    return row[col]
            return 0.0
    
    def _add_demographics(self, segments_df: pd.DataFrame, 
                         demographics_df: pd.DataFrame) -> pd.DataFrame:
        """Add demographic data to segments"""
        # For this example, we'll add sample demographics
        # In a real implementation, you'd do spatial joins
        
        segments_df['neighborhood'] = 'Loop'  # Default
        segments_df['population'] = 2500
        segments_df['median_income'] = 45000
        
        # Add some variation based on segment characteristics
        if 'mode' in segments_df.columns:
            # Transit segments in more populated areas
            transit_mask = segments_df['mode'] == 'transit'
            segments_df.loc[transit_mask, 'population'] = 4000
            segments_df.loc[transit_mask, 'median_income'] = 55000
            segments_df.loc[transit_mask, 'neighborhood'] = 'Near North Side'
        
        return segments_df
    
    def _add_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived metrics to the dataset"""
        # Accessibility score based on mode and demographics
        df['accessibility_score'] = self._calculate_accessibility_score(df)
        
        # Mobility equity score
        df['equity_score'] = self._calculate_equity_score(df)
        
        # Efficiency score
        df['efficiency_score'] = self._calculate_efficiency_score(df)
        
        # Add timestamp
        df['created_at'] = datetime.now()
        
        return df
    
    def _calculate_accessibility_score(self, df: pd.DataFrame) -> float:
        """Calculate accessibility score"""
        scores = []
        
        for _, row in df.iterrows():
            score = 0.5  # Base score
            
            # Mode-based adjustments
            if row.get('mode') == 'transit':
                score += 0.3
            elif row.get('mode') == 'walk':
                score += 0.2
            elif row.get('mode') == 'bike':
                score += 0.1
            
            # Income-based adjustments
            if 'median_income' in row and pd.notna(row['median_income']):
                if row['median_income'] > 60000:
                    score += 0.1
                elif row['median_income'] < 40000:
                    score -= 0.1
            
            scores.append(min(1.0, max(0.0, score)))
        
        return scores
    
    def _calculate_equity_score(self, df: pd.DataFrame) -> float:
        """Calculate mobility equity score"""
        scores = []
        
        for _, row in df.iterrows():
            score = 0.5  # Base score
            
            # Mode diversity
            if row.get('mode') in ['transit', 'walk', 'bike']:
                score += 0.2
            
            # Income accessibility
            if 'median_income' in row and pd.notna(row['median_income']):
                if row['median_income'] < 50000 and row.get('mode') in ['transit', 'walk']:
                    score += 0.3
            
            scores.append(min(1.0, max(0.0, score)))
        
        return scores
    
    def _calculate_efficiency_score(self, df: pd.DataFrame) -> float:
        """Calculate efficiency score"""
        scores = []
        
        for _, row in df.iterrows():
            score = 0.5  # Base score
            
            # Time efficiency
            if 'time_min' in row and pd.notna(row['time_min']):
                if row['time_min'] < 5:
                    score += 0.3
                elif row['time_min'] < 15:
                    score += 0.1
                else:
                    score -= 0.1
            
            # Mode efficiency
            if row.get('mode') == 'transit':
                score += 0.2
            elif row.get('mode') == 'bike':
                score += 0.1
            
            scores.append(min(1.0, max(0.0, score)))
        
        return scores
    
    def _ensure_schema_compliance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure dataset complies with schema"""
        # Ensure required columns exist
        for col, dtype in self.schema.items():
            if col not in df.columns:
                if dtype == 'string':
                    df[col] = ''
                elif dtype == 'float':
                    df[col] = 0.0
                elif dtype == 'int':
                    df[col] = 0
        
        # Convert types
        for col, dtype in self.schema.items():
            if col in df.columns:
                if dtype == 'string':
                    df[col] = df[col].astype(str)
                elif dtype == 'float':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                elif dtype == 'int':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        return df
    
    def get_dataset_summary(self) -> Dict:
        """Get summary statistics of the unified dataset"""
        if self.unified_df is None:
            return {}
        
        summary = {
            'total_segments': len(self.unified_df),
            'modes': self.unified_df['mode'].value_counts().to_dict(),
            'neighborhoods': self.unified_df['neighborhood'].value_counts().to_dict(),
            'avg_time_min': self.unified_df['time_min'].mean(),
            'avg_population': self.unified_df['population'].mean(),
            'avg_median_income': self.unified_df['median_income'].mean(),
            'data_sources': self.unified_df.get('data_source', {}).value_counts().to_dict()
        }
        
        return summary
    
    def export_to_csv(self, filepath: str) -> None:
        """Export unified dataset to CSV"""
        if self.unified_df is not None:
            self.unified_df.to_csv(filepath, index=False)
            print(f"Exported unified dataset to {filepath}")
        else:
            print("No unified dataset to export")
    
    def export_to_parquet(self, filepath: str) -> None:
        """Export unified dataset to Parquet"""
        if self.unified_df is not None:
            self.unified_df.to_parquet(filepath, index=False)
            print(f"Exported unified dataset to {filepath}")
        else:
            print("No unified dataset to export")


