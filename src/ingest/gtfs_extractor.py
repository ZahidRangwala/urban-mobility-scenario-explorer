"""
GTFS Data Extractor for Transit Analysis
Extracts transit routes, stops, and schedules for mobility analysis
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import requests
import zipfile
import io
import os
from typing import Dict, List, Tuple
import numpy as np

class GTFSExtractor:
    def __init__(self, gtfs_url: str, data_dir: str = "data/gtfs"):
        self.gtfs_url = gtfs_url
        self.data_dir = data_dir
        self.routes = None
        self.stops = None
        self.stop_times = None
        self.trips = None
        self.calendar = None
        
    def download_and_extract(self) -> str:
        """Download and extract GTFS data"""
        os.makedirs(self.data_dir, exist_ok=True)
        print(f"Downloading GTFS data from {self.gtfs_url}...")
        
        r = requests.get(self.gtfs_url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(self.data_dir)
        
        return self.data_dir
    
    def load_gtfs_tables(self) -> Dict[str, pd.DataFrame]:
        """Load all GTFS tables"""
        tables = {}
        
        # Load main tables
        table_files = {
            'routes': 'routes.txt',
            'stops': 'stops.txt', 
            'stop_times': 'stop_times.txt',
            'trips': 'trips.txt',
            'calendar': 'calendar.txt',
            'calendar_dates': 'calendar_dates.txt'
        }
        
        for table_name, filename in table_files.items():
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                try:
                    tables[table_name] = pd.read_csv(filepath)
                    print(f"Loaded {table_name}: {len(tables[table_name])} records")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
            else:
                print(f"File not found: {filename}")
        
        # Store as instance variables
        self.routes = tables.get('routes')
        self.stops = tables.get('stops')
        self.stop_times = tables.get('stop_times')
        self.trips = tables.get('trips')
        self.calendar = tables.get('calendar')
        
        return tables
    
    def create_transit_segments(self) -> pd.DataFrame:
        """Create transit segments with travel times"""
        if self.routes is None or self.stops is None:
            self.load_gtfs_tables()
        
        # Get route information
        route_info = self.routes[['route_id', 'route_short_name', 'route_long_name', 'route_type']].copy()
        
        # Get stop information with coordinates
        stop_info = self.stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']].copy()
        
        # Create stop pairs for each route
        transit_segments = []
        
        if self.trips is not None and self.stop_times is not None:
            # Get trip information
            trip_routes = self.trips[['trip_id', 'route_id']].copy()
            
            # Get stop sequences for each trip
            stop_sequences = self.stop_times[['trip_id', 'stop_id', 'stop_sequence', 'arrival_time']].copy()
            
            # Merge with route info
            trip_routes = trip_routes.merge(route_info, on='route_id', how='left')
            
            # Get stop sequences with route info
            stop_sequences = stop_sequences.merge(trip_routes, on='trip_id', how='left')
            stop_sequences = stop_sequences.merge(stop_info, on='stop_id', how='left')
            
            # Create segments between consecutive stops
            for route_id in stop_sequences['route_id'].unique():
                route_data = stop_sequences[stop_sequences['route_id'] == route_id]
                
                for trip_id in route_data['trip_id'].unique():
                    trip_data = route_data[route_data['trip_id'] == trip_id].sort_values('stop_sequence')
                    
                    if len(trip_data) > 1:
                        for i in range(len(trip_data) - 1):
                            from_stop = trip_data.iloc[i]
                            to_stop = trip_data.iloc[i + 1]
                            
                            # Calculate travel time
                            time_min = self._calculate_transit_time(
                                from_stop['arrival_time'], 
                                to_stop['arrival_time']
                            )
                            
                            # Calculate distance
                            distance_m = self._calculate_distance(
                                from_stop['stop_lat'], from_stop['stop_lon'],
                                to_stop['stop_lat'], to_stop['stop_lon']
                            )
                            
                            segment = {
                                'segment_id': f"transit_{route_id}_{from_stop['stop_id']}_{to_stop['stop_id']}",
                                'from_stop_id': from_stop['stop_id'],
                                'to_stop_id': to_stop['stop_id'],
                                'from_stop_name': from_stop['stop_name'],
                                'to_stop_name': to_stop['stop_name'],
                                'from_lat': from_stop['stop_lat'],
                                'from_lon': from_stop['stop_lon'],
                                'to_lat': to_stop['stop_lat'],
                                'to_lon': to_stop['stop_lon'],
                                'route_id': route_id,
                                'route_name': from_stop['route_long_name'],
                                'route_type': from_stop['route_type'],
                                'mode': 'transit',
                                'time_min': time_min,
                                'distance_m': distance_m,
                                'geometry': self._create_line_geometry(
                                    from_stop['stop_lat'], from_stop['stop_lon'],
                                    to_stop['stop_lat'], to_stop['stop_lon']
                                )
                            }
                            
                            transit_segments.append(segment)
        
        return pd.DataFrame(transit_segments)
    
    def _calculate_transit_time(self, from_time: str, to_time: str) -> float:
        """Calculate travel time between stops"""
        try:
            # Parse time strings (HH:MM:SS format)
            from_h, from_m, from_s = map(int, from_time.split(':'))
            to_h, to_m, to_s = map(int, to_time.split(':'))
            
            from_minutes = from_h * 60 + from_m + from_s / 60
            to_minutes = to_h * 60 + to_m + to_s / 60
            
            return to_minutes - from_minutes
        except:
            return 0.0
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Earth radius in meters
        r = 6371000
        return c * r
    
    def _create_line_geometry(self, lat1: float, lon1: float, lat2: float, lon2: float):
        """Create line geometry between two points"""
        from shapely.geometry import LineString
        return LineString([(lon1, lat1), (lon2, lat2)])
    
    def get_transit_network_summary(self) -> pd.DataFrame:
        """Get summary of transit network"""
        if self.routes is None:
            self.load_gtfs_tables()
        
        if self.routes is not None:
            summary = self.routes.groupby('route_type').agg({
                'route_id': 'count',
                'route_long_name': 'nunique'
            }).rename(columns={
                'route_id': 'num_routes',
                'route_long_name': 'unique_route_names'
            })
            
            # Add route type names
            route_types = {
                0: 'Tram/Light Rail',
                1: 'Subway/Metro', 
                2: 'Rail',
                3: 'Bus',
                4: 'Ferry',
                5: 'Cable Tram',
                6: 'Aerial Lift',
                7: 'Funicular',
                11: 'Trolleybus',
                12: 'Monorail'
            }
            
            summary['route_type_name'] = summary.index.map(route_types)
            
            return summary
        
        return pd.DataFrame()
