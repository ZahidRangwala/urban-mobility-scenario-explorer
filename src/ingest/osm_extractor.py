"""
OSM Data Extractor for Urban Mobility Analysis
Extracts detailed street network segments with travel time estimates
"""

import osmnx as ox
import geopandas as gpd
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple
import numpy as np

class OSMExtractor:
    def __init__(self, city_name: str):
        self.city_name = city_name
        self.graph = None
        self.nodes_gdf = None
        self.edges_gdf = None
        
    def fetch_network(self, network_type: str = "all") -> nx.MultiDiGraph:
        """Fetch OSM network for the city"""
        print(f"Fetching OSM network for {self.city_name}...")
        self.graph = ox.graph_from_place(self.city_name, network_type=network_type)
        return self.graph
    
    def extract_segments(self) -> gpd.GeoDataFrame:
        """Extract road segments with detailed attributes"""
        if self.graph is None:
            self.fetch_network()
            
        # Convert to GeoDataFrames
        nodes, edges = ox.graph_to_gdfs(self.graph)
        
        # Calculate travel times based on road type and length
        edges = self._calculate_travel_times(edges)
        
        # Add segment metadata
        edges = self._add_segment_metadata(edges)
        
        self.edges_gdf = edges
        self.nodes_gdf = nodes
        
        return edges
    
    def _calculate_travel_times(self, edges: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Calculate travel times for different modes"""
        # Speed limits by road type (km/h)
        speed_limits = {
            'motorway': 110,
            'trunk': 90,
            'primary': 60,
            'secondary': 50,
            'tertiary': 40,
            'residential': 30,
            'unclassified': 30,
            'service': 20,
            'footway': 5,
            'cycleway': 15,
            'path': 5
        }
        
        # Calculate length in meters
        edges['length_m'] = edges.geometry.length
        
        # Handle highway column - convert lists to strings and clean data
        if 'highway' in edges.columns:
            # Convert lists to strings and handle multiple values
            edges['highway_clean'] = edges['highway'].apply(self._clean_highway_value)
        else:
            edges['highway_clean'] = 'unclassified'
        
        # Assign speeds and calculate travel times
        edges['speed_kmh'] = edges['highway_clean'].map(speed_limits).fillna(30)
        edges['time_drive_min'] = (edges['length_m'] / 1000) / (edges['speed_kmh'] / 60)
        edges['time_walk_min'] = (edges['length_m'] / 1000) / (5 / 60)  # 5 km/h walking
        edges['time_bike_min'] = (edges['length_m'] / 1000) / (15 / 60)  # 15 km/h cycling
        
        return edges
    
    def _clean_highway_value(self, value):
        """Clean highway values that might be lists or have multiple values"""
        try:
            # Handle NaN values
            if pd.isna(value):
                return 'unclassified'
            
            # Handle numpy arrays
            if hasattr(value, '__len__') and not isinstance(value, str):
                if len(value) == 0:
                    return 'unclassified'
                # Take the first element if it's an array/list
                value = value[0] if hasattr(value, '__getitem__') else value
            
            # Handle lists
            if isinstance(value, list):
                return str(value[0]) if value else 'unclassified'
            
            # Handle strings
            if isinstance(value, str):
                # Handle multiple values separated by semicolons
                if ';' in value:
                    return value.split(';')[0].strip()
                return value
            
            # Convert to string as fallback
            return str(value) if value is not None else 'unclassified'
            
        except Exception as e:
            # If anything goes wrong, return unclassified
            return 'unclassified'
    
    def _add_segment_metadata(self, edges: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Add segment metadata for analysis"""
        # Create segment IDs - handle MultiIndex properly
        if isinstance(edges.index, pd.MultiIndex):
            # OSMnx returns (u, v, key) MultiIndex
            edges['segment_id'] = [f"{u}_{v}" for u, v, k in edges.index]
        else:
            edges['segment_id'] = edges.index.astype(str)
        
        # Add from/to node information
        edges['from_node'] = edges['u'].astype(str)
        edges['to_node'] = edges['v'].astype(str)
        
        # Add mode information
        edges['mode'] = edges['highway_clean'].apply(self._determine_mode)
        
        # Add accessibility flags
        edges['is_walkable'] = edges['highway_clean'].isin(['footway', 'path', 'residential', 'tertiary', 'secondary', 'primary'])
        edges['is_cyclable'] = edges['highway_clean'].isin(['cycleway', 'residential', 'tertiary', 'secondary', 'primary', 'trunk'])
        edges['is_drivable'] = ~edges['highway_clean'].isin(['footway', 'path', 'cycleway'])
        
        return edges
    
    def _determine_mode(self, highway_type: str) -> str:
        """Determine primary mode for segment"""
        if pd.isna(highway_type):
            return 'unknown'
        
        if highway_type in ['motorway', 'trunk', 'primary']:
            return 'car'
        elif highway_type in ['cycleway']:
            return 'bike'
        elif highway_type in ['footway', 'path']:
            return 'walk'
        else:
            return 'mixed'
    
    def get_segments_for_analysis(self) -> pd.DataFrame:
        """Get segments formatted for mobility analysis"""
        if self.edges_gdf is None:
            self.extract_segments()
        
        # Select relevant columns for analysis
        analysis_cols = [
            'segment_id', 'from_node', 'to_node', 'mode', 'highway',
            'length_m', 'time_drive_min', 'time_walk_min', 'time_bike_min',
            'is_walkable', 'is_cyclable', 'is_drivable', 'geometry'
        ]
        
        segments = self.edges_gdf[analysis_cols].copy()
        
        # Add coordinates for from/to points
        if self.nodes_gdf is not None:
            segments = self._add_coordinates(segments)
        
        return segments
    
    def _add_coordinates(self, segments: pd.DataFrame) -> pd.DataFrame:
        """Add coordinate information for from/to nodes"""
        # Get node coordinates
        node_coords = self.nodes_gdf[['x', 'y']].to_dict('index')
        
        # Add from coordinates
        segments['from_lon'] = segments['from_node'].map(lambda x: node_coords.get(int(x), {}).get('x', 0))
        segments['from_lat'] = segments['from_node'].map(lambda x: node_coords.get(int(x), {}).get('y', 0))
        
        # Add to coordinates  
        segments['to_lon'] = segments['to_node'].map(lambda x: node_coords.get(int(x), {}).get('x', 0))
        segments['to_lat'] = segments['to_node'].map(lambda x: node_coords.get(int(x), {}).get('y', 0))
        
        return segments
