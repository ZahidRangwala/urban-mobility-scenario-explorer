"""
Census Data Extractor for Demographics
Extracts population and income data for neighborhood analysis
"""

import pandas as pd
import geopandas as gpd
import requests
import json
from typing import Dict, List, Tuple
import numpy as np
from shapely.geometry import Point, Polygon

class CensusExtractor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.census.gov/data"
        self.year = "2022"  # Most recent ACS data
        
    def get_tract_demographics(self, state_fips: str, county_fips: str = None) -> pd.DataFrame:
        """Get census tract demographics for a state/county"""
        
        # ACS variables for demographics
        variables = {
            'B01003_001E': 'total_population',
            'B19013_001E': 'median_household_income',
            'B08301_010E': 'public_transportation_commuters',
            'B08301_001E': 'total_commuters',
            'B08301_003E': 'drove_alone_commuters',
            'B08301_004E': 'carpool_commuters',
            'B08301_010E': 'public_transport_commuters',
            'B08301_011E': 'walked_commuters',
            'B08301_012E': 'bicycle_commuters'
        }
        
        # Build API request
        if self.api_key:
            url = f"{self.base_url}/{self.year}/acs/acs5"
            params = {
                'get': ','.join(variables.keys()),
                'for': 'tract:*',
                'in': f'state:{state_fips}',
                'key': self.api_key
            }
        else:
            # Use sample data if no API key
            return self._get_sample_demographics()
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Rename columns
            df = df.rename(columns=variables)
            
            # Convert numeric columns
            numeric_cols = ['total_population', 'median_household_income', 'total_commuters',
                           'drove_alone_commuters', 'carpool_commuters', 'public_transport_commuters',
                           'walked_commuters', 'bicycle_commuters']
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Calculate derived metrics
            df['transit_share'] = df['public_transport_commuters'] / df['total_commuters']
            df['walk_bike_share'] = (df['walked_commuters'] + df['bicycle_commuters']) / df['total_commuters']
            df['car_share'] = (df['drove_alone_commuters'] + df['carpool_commuters']) / df['total_commuters']
            
            # Add geographic identifiers
            df['state_fips'] = state_fips
            df['county_fips'] = df['county']
            df['tract_fips'] = df['tract']
            df['geoid'] = df['state_fips'] + df['county_fips'] + df['tract_fips']
            
            return df
            
        except Exception as e:
            print(f"Error fetching census data: {e}")
            return self._get_sample_demographics()
    
    def _get_sample_demographics(self) -> pd.DataFrame:
        """Generate sample demographics data for testing"""
        print("Using sample demographics data (no API key provided)")
        
        # Sample data for Chicago area
        sample_data = {
            'geoid': ['17031010100', '17031010200', '17031010300', '17031010400', '17031010500'],
            'total_population': [2500, 3200, 1800, 4100, 2900],
            'median_household_income': [45000, 62000, 38000, 75000, 52000],
            'total_commuters': [1200, 1500, 900, 2000, 1400],
            'drove_alone_commuters': [800, 900, 600, 1200, 900],
            'carpool_commuters': [150, 200, 100, 250, 180],
            'public_transport_commuters': [200, 300, 150, 400, 250],
            'walked_commuters': [30, 50, 30, 80, 40],
            'bicycle_commuters': [20, 50, 20, 70, 30],
            'transit_share': [0.167, 0.200, 0.167, 0.200, 0.179],
            'walk_bike_share': [0.042, 0.067, 0.056, 0.075, 0.050],
            'car_share': [0.792, 0.733, 0.778, 0.725, 0.771],
            'state_fips': ['17'] * 5,
            'county_fips': ['031'] * 5,
            'tract_fips': ['010100', '010200', '010300', '010400', '010500']
        }
        
        return pd.DataFrame(sample_data)
    
    def get_neighborhood_boundaries(self, city: str) -> gpd.GeoDataFrame:
        """Get neighborhood boundaries (using sample data)"""
        # Sample neighborhood boundaries for Chicago
        neighborhoods = {
            'name': ['Loop', 'Near North Side', 'Lincoln Park', 'Lakeview', 'Wicker Park'],
            'geometry': [
                Polygon([(-87.6298, 41.8781), (-87.6298, 41.8881), (-87.6198, 41.8881), (-87.6198, 41.8781)]),
                Polygon([(-87.6398, 41.8881), (-87.6398, 41.8981), (-87.6298, 41.8981), (-87.6298, 41.8881)]),
                Polygon([(-87.6498, 41.8981), (-87.6498, 41.9081), (-87.6398, 41.9081), (-87.6398, 41.8981)]),
                Polygon([(-87.6598, 41.9081), (-87.6598, 41.9181), (-87.6498, 41.9181), (-87.6498, 41.9081)]),
                Polygon([(-87.6698, 41.9181), (-87.6698, 41.9281), (-87.6598, 41.9281), (-87.6598, 41.9181)])
            ]
        }
        
        gdf = gpd.GeoDataFrame(neighborhoods, crs='EPSG:4326')
        return gdf
    
    def assign_demographics_to_segments(self, segments: pd.DataFrame, demographics: pd.DataFrame) -> pd.DataFrame:
        """Assign demographic data to segments based on location"""
        # For this example, we'll assign demographics based on segment location
        # In a real implementation, you'd do spatial joins
        
        # Sample assignment logic
        segments['neighborhood'] = 'Loop'  # Default neighborhood
        segments['population'] = 2500     # Default population
        segments['median_income'] = 45000  # Default income
        
        # Add some variation based on segment location
        if 'from_lat' in segments.columns and 'from_lon' in segments.columns:
            # Simple assignment based on coordinates
            segments.loc[segments['from_lat'] > 41.9, 'neighborhood'] = 'Lakeview'
            segments.loc[segments['from_lat'] > 41.9, 'population'] = 3200
            segments.loc[segments['from_lat'] > 41.9, 'median_income'] = 62000
            
            segments.loc[segments['from_lat'] < 41.85, 'neighborhood'] = 'Near North Side'
            segments.loc[segments['from_lat'] < 41.85, 'population'] = 1800
            segments.loc[segments['from_lat'] < 41.85, 'median_income'] = 38000
        
        return segments
