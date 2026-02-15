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
    default=region_list
)

df = df[
    (df["WEEKLY_REVISED"] >= pd.Timestamp(date_range[0])) &
    (df["WEEKLY_REVISED"] <= pd.Timestamp(date_range[1])) &
    (df["INDUSTRY"].isin(selected_industries)) &
    (df["REGION"].isin(selected_regions))
]

# ==========================================================
# EXECUTIVE KPIs
# ==========================================================

st.title("📊 monday.com CRO Strategic Hiring Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Net WAPP", f"{int(df['NET_WAPP'].sum()):,}")
col2.metric("New WAPP", f"{int(df['WAPP_NEW'].sum()):,}")
col3.metric("Resurrect WAPP", f"{int(df['WAPP_RESURRECT'].sum()):,}")
col4.metric("Churn WAPP", f"{int(df['WAPP_CHURN'].sum()):,}")

st.markdown("---")

# ==========================================================
# INDUSTRY BREAKDOWN (ALL COMPONENTS)
# ==========================================================

st.header("Industry WAPP Breakdown")

industry = df.groupby("INDUSTRY").agg(
    New=("WAPP_NEW","sum"),
    Resurrect=("WAPP_RESURRECT","sum"),
    Churn=("WAPP_CHURN","sum"),
    Net=("NET_WAPP","sum")
).reset_index().sort_values("Net", ascending=False)

st.dataframe(industry, use_container_width=True)

fig1 = px.bar(
    industry.head(10),
    x="INDUSTRY",
    y=["New", "Resurrect", "Churn"],
    title="New vs Resurrect vs Churn by Industry",
    barmode="group",
    color_discrete_sequence=["#6161FF", "#00CA72", "#FB275D"]
)

st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# ==========================================================
# WEEKLY TREND (ALL COMPONENTS)
# ==========================================================

st.header("Weekly WAPP Trend (Revised Week)")

weekly = df.groupby("WEEKLY_REVISED").agg(
    New=("WAPP_NEW","sum"),
    Resurrect=("WAPP_RESURRECT","sum"),
    Churn=("WAPP_CHURN","sum"),
    Net=("NET_WAPP","sum")
).reset_index()

fig2 = px.line(
    weekly,
    x="WEEKLY_REVISED",
    y=["New", "Resurrect", "Churn", "Net"],
    title="Weekly New, Resurrect, Churn & Net WAPP",
    color_discrete_sequence=["#6161FF", "#00CA72", "#FB275D", "#FFCC00"]
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ==========================================================
# REGIONAL BREAKDOWN (ALL COMPONENTS)
# ==========================================================

st.header("Regional WAPP Breakdown")

regional = df.groupby("REGION").agg(
    New=("WAPP_NEW","sum"),
    Resurrect=("WAPP_RESURRECT","sum"),
    Churn=("WAPP_CHURN","sum"),
    Net=("NET_WAPP","sum")
).reset_index()

fig3 = px.bar(
    regional,
    x="REGION",
    y=["New", "Resurrect", "Churn"],
    title="New vs Resurrect vs Churn by Region",
    barmode="group",
    color_discrete_sequence=["#6161FF", "#00CA72", "#FB275D"]
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.markdown("Built for CRO strategic hiring • Global allocation • monday.com inspired theme")

