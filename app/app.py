import streamlit as st
import pandas as pd
import os

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(page_title="National Parks Explorer", layout="wide")
st.title("🌲 National Parks Explorer")

# -----------------------------
# Load JSON data
# -----------------------------
DATA_PATH = os.path.join("data", "national_parks_weather.json")

@st.cache_data
def load_data(path):
    return pd.read_json(path)

df = load_data(DATA_PATH)

# -----------------------------
# Create derived columns
# -----------------------------
if "state" not in df.columns:
    df["state"] = df.get("states", "").str.split(",").str[-1].str.strip()

# Drop rows without coordinates for mapping
df = df.dropna(subset=["latitude", "longitude"], how="all")

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")

# Dynamic filters: state and weather condition
filter_fields = ["state", "condition"]
filters = {}
for field in filter_fields:
    if field in df.columns:
        unique_vals = df[field].dropna().unique()
        filters[field] = st.sidebar.selectbox(
            f"Filter by {field}",
            ["All"] + sorted(unique_vals)
        )

# Apply filters
filtered_df = df.copy()
for field, value in filters.items():
    if value != "All":
        filtered_df = filtered_df[filtered_df[field] == value]

# -----------------------------
# Park selection for details
# -----------------------------
st.sidebar.header("Select a Park for Details")
if not filtered_df.empty:
    park_names = filtered_df["fullName"].tolist()
    selected_park = st.sidebar.selectbox("Choose a park", ["None"] + park_names)
else:
    selected_park = "None"

# -----------------------------
# Top Metrics
# -----------------------------
st.subheader("📊 Quick Stats")
col1, col2, col3 = st.columns(3)

col1.metric("Total Parks", len(filtered_df))

if "temperature_f" in filtered_df.columns:
    avg_temp = filtered_df["temperature_f"].mean()
    col2.metric("Avg Temp (°F)", round(avg_temp, 1))
else:
    col2.metric("Avg Temp (°F)", "N/A")

if "condition" in filtered_df.columns:
    col3.metric("Unique Weather Types", filtered_df["condition"].nunique())
else:
    col3.metric("Unique Weather Types", "N/A")

# -----------------------------
# Main layout: Map + Weather Chart
# -----------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Parks Map")
    if "latitude" in filtered_df.columns and "longitude" in filtered_df.columns:
        st.map(filtered_df[["latitude", "longitude"]].dropna())
    else:
        st.write("No coordinates available for mapping.")

with col2:
    st.subheader("🌤️ Weather Breakdown")
    if "condition" in filtered_df.columns:
        weather_counts = filtered_df["condition"].value_counts()
        st.bar_chart(weather_counts)
    else:
        st.write("No weather data available.")

# -----------------------------
# Display all fields dynamically
# -----------------------------
st.subheader("📋 Parks Data")
columns = st.multiselect(
    "Select columns to display",
    options=filtered_df.columns,
    default=filtered_df.columns.tolist()
)
st.dataframe(filtered_df[columns])

# -----------------------------
# Selected Park Detail View
# -----------------------------
if selected_park != "None":
    st.subheader(f"🏞️ {selected_park}")

    park_data = filtered_df[filtered_df["fullName"] == selected_park].iloc[0]

    # Show description
    if "description" in park_data and pd.notna(park_data["description"]):
        st.write(park_data["description"])

    # Show official website
    if "url" in park_data and pd.notna(park_data["url"]):
        st.markdown(f"[Official Website]({park_data['url']})")

    # Show images (up to 3)
    if "images" in park_data and isinstance(park_data["images"], list):
        for img in park_data["images"][:3]:
            st.image(img.get("url"), caption=img.get("caption", ""), width=True)

    # Show all other fields dynamically
    with st.expander("Other info"):
        extra_fields = park_data.drop(labels=["fullName", "description", "url", "images"])
        st.json(extra_fields.to_dict())