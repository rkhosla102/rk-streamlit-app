import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="monday.com CRO Hiring Dashboard", layout="wide")

# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data
def load_data():
    df = pd.read_csv("wapp_data.csv")

    df["WEEKLY_REVISED"] = pd.to_datetime(df["WEEKLY_REVISED"], errors="coerce")

    numeric_cols = ["WAPP_NEW", "WAPP_RESURRECT", "WAPP_CHURN", "WAPP"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["INDUSTRY"] = df["INDUSTRY"].astype(str)
    df = df[df["INDUSTRY"].str.strip() != ""]

    df["REGION"] = df["REGION"].fillna("NA").replace("nan", "NA").astype(str)

    df["NET_WAPP"] = df["WAPP_NEW"] + df["WAPP_RESURRECT"] - df["WAPP_CHURN"]

    return df

df = load_data()

# ==========================================================
# SIDEBAR FILTERS
# ==========================================================

st.sidebar.header("Filters")

min_date = df["WEEKLY_REVISED"].min()
max_date = df["WEEKLY_REVISED"].max()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

industry_list = sorted(df["INDUSTRY"].unique())
region_list = sorted(df["REGION"].unique())

selected_industries = st.sidebar.multiselect(
    "Industries",
    industry_list,
    default=industry_list
)

selected_regions = st.sidebar.multiselect(
    "Regions",
    region_list,
    defau

st.markdown("---")
st.markdown("Built for CRO strategic hiring • Global & Regional Allocation • monday.com Executives")

