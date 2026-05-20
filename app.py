# 1. Setting up the environment
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# Using “wide” makes layout easier
st.set_page_config(
    layout="wide" ,
    page_title="Dublin Rental Guide Dashboard",
    page_icon="🏙",
    initial_sidebar_state="expanded"
)
# 2. CSS styles
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .dashboard-title {
        font-family: 'DM Serif Display', serif;
        font-size: 2.2rem;
        color: #1a1a2e;
        margin-bottom: 0;
    }
    .dashboard-subtitle {
        font-size: 0.95rem;
        color: #6b7280;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }
    .section-heading {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #9ca3af;
        margin-bottom: 0.5rem;
    }
    .advanced-label {
        display: inline-block;
        background: #1a1a2e;
        color: white;
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 0.6rem;
    }
    .stTabs [data-baseweb="tab"] { font-size: 0.85rem; }
    .stSidebar { background-color: #fafafa; }
    div[data-testid="metric-container"] { display: none; }
</style>
""", unsafe_allow_html=True)

# 3. Load data
# Cache the return value of the function to speed up file reading
@st.cache_data
def load_data():
    df = pd.read_csv("dataset/dublin_rent_detail.csv")
    coords = pd.read_csv("dataset/district_coordinates.csv")
    return df, coords

df, coords = load_data()

# 4.Sidebar
# Place the content in the left-hand sidebar
with st.sidebar:
    st.markdown(
        '<div class="dashboard-title" style="font-size:1.3rem">🛠 Filters</div>', unsafe_allow_html=True)
    st.markdown("---")

# In a fixed order, from common to uncommon
    all_property_types = [
        "Apartment",
        "Other flats",
        "Terrace house",
        "Semi detached house",
        "Detached house",
    ]
    property_type = st.selectbox("Property Type", all_property_types)

    bedroom_order = ["One bed", "Two bed", "Three bed", "Four plus bed"]
    # Cascading Filter: bedrooms are updated in real time as property types change
    available_bedrooms = [
        b for b in bedroom_order
        if b in df[df["Property_type"] == property_type]["Bedrooms"].unique()
    ]
    bedrooms = st.selectbox("Bedrooms", available_bedrooms)
    # Dual slider, allowing users to freely select a date range
    year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
    year_range = st.slider("Year Range", year_min, year_max, (year_min, year_max))
    # Single slider, allowing users to select a range for their rental budget
    budget = st.slider("Max Monthly Budget (€)", 500, 5000, 2500, step=100)
    st.markdown("---")
    # Dynamic configurations：Users select analysis parameters according to their needs, charts and summary metrics are updated in real time based on the user’s settings
    st.markdown('<div class="section-heading">Display Metric</div>', unsafe_allow_html=True)
    metric_type = st.radio("", ["Median", "Mean"], horizontal=True)
    agg_func = "median" if metric_type == "Median" else "mean"
    # Conditional content：Users can control whether content is shown or hidden according to their needs
    st.markdown("---")
    show_raw_data = st.checkbox("Show Data Table")
# Connected visualisations：All charts use the same filtered variable
# 5. Data filtering
# 5.1 Master data:
filtered = df[
    (df["Property_type"] == property_type) &
    (df["Bedrooms"] == bedrooms) &
    (df["Year"] >= year_range[0]) &
    (df["Year"] <= year_range[1])
]
# 5.2 Processing map-specific data
# Identify the year with the highest value in the filtered data. if the result is empty, use the data for 2024
latest_year = filtered["Year"].max() 
if len(filtered) > 0:
    latest_year = filtered["Year"].max()
else:
    latest_year = year_max
# The map only displays property listings from the most recent year; as users are only interested in properties currently available to rent, there is no need to show data from previous years
map_data = filtered[filtered["Year"] == latest_year]
# Group the data by district
district_agg = map_data.groupby("District")["Rent"].agg(agg_func).reset_index()
district_agg.columns = ["District", "Rent"]
# Join the `district_agg` and `coords` tables based on the `district` field, merge the latitude and longitude coordinates, and define the map boundaries
district_agg = district_agg.merge(coords, left_on="District", right_on="district", how="left")
# 'Affordable' will subsequently determine the colour of the bar chart and the “Districts within budget” section in the KPI card
district_agg["affordable"] = district_agg["Rent"] <= budget
# budget_gap is used to control the shade of the map
district_agg["budget_gap"] = budget - district_agg["Rent"]

st.markdown('<div class="dashboard-title">Dublin Rental Market Explorer</div>', unsafe_allow_html=True)

st.markdown('<div class="advanced-label">Summary Metrics</div>', unsafe_allow_html=True)

# Calculates the number of affordable properties and the current median rent; if the user’s search criteria are too restrictive to allow for a calculation, the data is displayed as zero
affordable_count = district_agg["affordable"].sum() 
if len(district_agg) > 0:
    affordable_count = district_agg["affordable"].sum()
else:
    affordable_count = 0
total_districts = len(district_agg)
median_rent_now = round(district_agg["Rent"].median(), 0) 
if len(district_agg) > 0:
    median_rent_now = round(district_agg["Rent"].median(), 0)
else:
    median_rent_now = 0

# 6.KPI
# Set up three KPI cards
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Districts within budget", f"{affordable_count}/{total_districts}")
with c2:
    st.metric(f"{metric_type} rent ({latest_year})", f"€{int(median_rent_now):,}")
with c3:
    st.metric("Your max budget", f"€{budget:,}")
st.markdown("<br>", unsafe_allow_html=True)


with open("dataset/dublin_districts.geojson") as f:
    geojson = json.load(f)

# 7.Main View
# Map and bar chart layout
col_map, col_bar = st.columns([2, 1], gap="medium")

# 7.1 Map
with col_map:
    st.markdown("### Rental Map")
    fig_map = px.choropleth_mapbox(
        district_agg,
        # Match District column with GeoJSON boundaries
        geojson=geojson,
        locations="District",
        featureidkey="properties.district",
        # Determine the area colour based on the budget surplus
        color="budget_gap",
        color_continuous_scale=["#ef4444", "#fbbf24", "#10b981"],
        # Define the gradient range to ensure the colours are clearly distinguishable
        range_color=(-1000, 1000),
        mapbox_style="carto-positron",
        # After repeatedly adjusting the zoom to 9 and shifting the centre slightly downwards, the display area appears optimal
        zoom=9,
        center={"lat": 53.32, "lon": -6.27},
        opacity=0.75,
        # Hover over to display district, rent and budget gap
        hover_name="District",
        hover_data={"Rent": ":,.0f", "budget_gap": ":,.0f"},
        height=500,
    )
    st.plotly_chart(fig_map, use_container_width=True)

# 7.2 Bar chart: horizontal layout fits better in the narrow right column
with col_bar:
    st.markdown("### Rent by District")
    fig_bar = px.bar(
        # Sort the rent from lowest to highest to align with user expectations
        district_agg.sort_values("Rent", ascending=False),
        x="Rent",
        y="District",
        orientation="h",
        # Use “affordable” to determine the colour
        color="affordable",
        color_discrete_map={True: "#10b981", False: "#ef4444"},
        labels={"Rent": f"{metric_type} Rent (€)", "affordable": "Within budget"},
        height=500,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# 8.Supporting Charts
# Tabs
st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🔴 Rent Trend", "🟠 Price Range", "🟢 Rent Matrix", "🔵 Bedroom Cost"]) 

# 8.1 Line chart
with tab1:
   
    st.markdown("### Rent Trend Over Time")
    # Displaying data for all regions makes the line chart cluttered and difficult to read; users can select regions according to their needs, which improves clarity and offers greater flexibility
    trend_data = filtered.groupby(["Year", "District"])["Rent"].agg(agg_func).reset_index()
    # Sort districts in numerical order (D1 to D24) instead of alphabetical order
    district_order = ["D1", "D2", "D3", "D4", "D5", "D6", "D6W", "D7", "D8", "D9",
                  "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17", "D18",
                  "D20", "D22", "D24"]
    all_districts = [d for d in district_order if d in trend_data["District"].unique()]
    selected_districts = st.multiselect(
        "Select Districts to Compare",
        all_districts,
        default=all_districts[:5]
    )
    trend_data = trend_data[trend_data["District"].isin(selected_districts)]
    fig_line = px.line(
        trend_data, x="Year", y="Rent", color="District",
        labels={"Rent": f"{metric_type} Rent (€)"},
        height=450,
    )
    st.plotly_chart(fig_line, use_container_width=True)
   

# 8.2 Box plot
with tab2:
    st.markdown("### Rent Range by Property Type")
    # Using the raw data from `df` rather than `filter`, with the primary variable being the year, so filtering by year retains all property types
    box_data = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
    fig_box = px.box(
        box_data, x="Property_type", y="Rent",
        color="Property_type",
        labels={"Rent": "Monthly Rent (€)", "Property_type": ""},
        height=400,
    )
    st.plotly_chart(fig_box, use_container_width=True)

# 8.3 Heatmap
with tab3:
    st.markdown("### Rent by District and Bedroom Count")
    # Using the raw data from df, filter the data by year only, and group it simultaneously by the two variables: region and property type
    heat_data = df[
        (df["Year"] >= year_range[0]) & 
        (df["Year"] <= year_range[1])
    ].groupby(["District", "Bedrooms"])["Rent"].median().reset_index()
    heat_pivot = heat_data.pivot(index="District", columns="Bedrooms", values="Rent")
    # Sort districts in numerical order (D1 to D24) instead of alphabetical order
    district_order = ["D1", "D2", "D3", "D4", "D5", "D6", "D6W", "D7", "D8", "D9",
    "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17", "D18","D20", "D22", "D24"]
    heat_pivot = heat_pivot.reindex([d for d in district_order if d in heat_pivot.index])  
    bedroom_order = ["One bed", "Two bed", "Three bed", "Four plus bed"]
    heat_pivot = heat_pivot[[c for c in bedroom_order if c in heat_pivot.columns]]
    fig_heat = px.imshow(
        heat_pivot,
        # Colour gradient scheme
        color_continuous_scale="RdYlGn_r",
        labels=dict(color="Median Rent (€)"),
        # Set it to auto, otherwise the table will be too small
        aspect="auto",
        height=600,
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# 8.4 Scatter 
with tab4:
    st.markdown("### Cost of an Extra Bedroom by District")
    one_bed = df[
        (df["Bedrooms"] == "One bed") & (df["Year"] == latest_year)
    ].groupby("District")["Rent"].median().reset_index()
    one_bed.columns = ["District", "One bed"]
    two_bed = df[
        (df["Bedrooms"] == "Two bed") & (df["Year"] == latest_year)
    ].groupby("District")["Rent"].median().reset_index()
    two_bed.columns = ["District", "Two bed"]
    # Group by district name and merge the data for the same district from the `one_bed` and `two_bed` tables into a single row
    scatter_df = one_bed.merge(two_bed, on="District").dropna()
    fig_scatter = px.scatter(
        scatter_df, x="One bed", y="Two bed",
        text="District",
        labels={"One bed": "One bed (€)", "Two bed": "Two bed (€)"},
        height=500,
    )
    # The district names and the scatter plot are jumbled together, making them difficult to read, so moved the district names above the scatter plot
    fig_scatter.update_traces(
    textposition="top center",
    marker=dict(size=8, opacity=0.7),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# 9.Download data table
st.markdown("<br>", unsafe_allow_html=True)

if show_raw_data:
    st.markdown("### Filtered Dataset")
    table_data = filtered[["Year", "District", "Location", "Property_type", "Bedrooms", "Rent"]].copy()
    # Data filtered and sorted by year and district
    table_data = table_data.sort_values(["Year", "District"])
    st.dataframe(
        table_data,
        use_container_width=True,
        height=320,
    )
    
    st.download_button(
        label="⬇ Download filtered data as CSV",
        data=table_data.to_csv(index=False),
        # Display the file name based on the property type and number of bedrooms selected by the user
        file_name=f"dublin_rent_{property_type.replace(' ', '_')}_{bedrooms.replace(' ', '_')}.csv",
        mime="text/csv",
    )
# 10.Set up footer 
st.markdown("---")
st.markdown("Data source: RIA02 - RTB Average Monthly Rent Report(CSO) · Republic of Ireland · 2008–2024")