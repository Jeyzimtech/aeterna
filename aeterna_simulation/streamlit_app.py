import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Aeterna Sol-IV Dashboard", layout="wide", page_icon="☀️")

st.title("☀️ Project Aeterna Sol-IV: Digital Twin Dashboard")
st.markdown("**Modular CSP-Based Water-Energy Infrastructure System**")

@st.cache_data
def load_data():
    return pd.read_csv("simulation_data.csv")

df = load_data()

# KPI Metrics
st.header("72-Hour Performance Metrics")
col1, col2, col3, col4 = st.columns(4)
total_elec_gen = df['Electricity Generated (MWh_e)'].sum()
total_elec_exp = df['Electricity Exported (MWh_e)'].sum()
total_water = df['Total Treated Water (m3)'].sum()
avg_tes = df['TES State of Charge (%)'].mean()

col1.metric("Electricity Generated", f"{total_elec_gen:.2f} MWh")
col2.metric("Electricity Exported", f"{total_elec_exp:.2f} MWh")
col3.metric("Total Treated Water", f"{total_water:,.0f} m³")
col4.metric("Average TES SOC", f"{avg_tes:.1f}%")

st.divider()

# Charts
st.header("System Telemetry")

tab1, tab2, tab3 = st.tabs(["⚡ Energy Subsystem", "💧 Desalination & Treatment", "🔋 Thermal Storage"])

with tab1:
    st.subheader("Electricity Profile")
    st.line_chart(df.set_index("Time (h)")[['Electricity Generated (MWh_e)', 'Electricity Exported (MWh_e)']])

with tab2:
    st.subheader("Water Production Profile")
    st.area_chart(df.set_index("Time (h)")[['Water Produced RO (m3)', 'Water Produced MED (m3)', 'Water Produced AD (m3)']])

with tab3:
    st.subheader("Thermal Energy Storage (TES) State of Charge")
    st.line_chart(df.set_index("Time (h)")['TES State of Charge (%)'])

st.divider()

# Data Viewer
with st.expander("View Raw Simulation Data"):
    st.dataframe(df)

