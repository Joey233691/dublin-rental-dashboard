# Dublin Rental Market Explorer

An interactive dashboard built with Streamlit to explore private rental market trends across Dublin's postal districts (2008–2024).

**Live demo:** https://dublin-rental-dashboard-bydkbjmcnakhvg6gwrzsx6.streamlit.app/

---

## Overview

This dashboard transforms official Residential Tenancies Board (RTB) data into an accessible decision-support tool for tenants, housing policymakers, and researchers. Users can explore how rents vary by district, property type, bedroom count, and year — with real-time filtering and geographic visualisation.

## Features

- **Choropleth map** — visualises rental affordability by district based on user budget
- **Cascading filters** — bedroom options update dynamically based on selected property type
- **Rent trend chart** — tracks rent changes from 2008 to 2024 across selected districts
- **Price range chart** — compares rent distribution by property type
- **Rent matrix heatmap** — shows median rent by district and bedroom count
- **Bedroom premium chart** — compares one-bedroom vs two-bedroom rents by district
- **Interactive data table** — filterable and sortable dataset view
- **Data export** — download filtered data as CSV

## Data Source

Residential Tenancies Board (RTB) — Republic of Ireland · 2008–2024

## Tech Stack

- Python
- Streamlit
- Plotly
- Pandas

## How to Run Locally

```bash
git clone https://github.com/Joey233691/dublin-rental-dashboard.git
cd dublin-rental-dashboard
pip install -r requirements.txt
streamlit run app.py
```
