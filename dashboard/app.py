import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Urban Mobility Scenario Explorer", layout="wide")
st.title("🚦 Urban Mobility Scenario Explorer")

st.sidebar.header("Scenario Controls")
scenario = st.sidebar.selectbox("Select a scenario", ["Baseline", "Add Bike Lanes", "Close Major Road"])
city = st.sidebar.text_input("City", "Chicago, Illinois")

st.write(f"### Current Scenario: {scenario} in {city}")

m = folium.Map(location=[41.8781, -87.6298], zoom_start=11)
folium.Marker([41.8781, -87.6298], tooltip="Downtown Chicago").add_to(m)
st_folium(m, width=900, height=600)
