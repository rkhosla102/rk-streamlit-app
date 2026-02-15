import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="monday.com CRO Hiring Dashboard",
    layout="wide"
)

# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data
def load_data():
    df = pd.read_csv("wapp_data.csv")

    # Clean date
    df["WEEKLY_REVISED"] = pd.to_datetime(df["WEEKLY_REVISED"], errors="coerce")

    # Convert numeric safely
    numeric_cols = ["WAPP_NEW", "WAPP_RESURRECT", "WAPP_CHURN", "WAPP"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Clean Industry
    df["INDUSTRY"] = df["INDUSTRY"].astype(str)
    df = df[df["INDUSTRY"].str.strip() != ""]

    # Clean Region (fix nan issue)
    df["REGION"] = df["REGION"].fillna("NA")
    df["REGION"] = df["REGION"].replace("nan", "NA")
    df["REGION"] = df["REGION"].astype(str)

    # Create Net WAPP
    df["NET_WAPP"] = df["WAPP_NEW"] + df["WAPP_RESURRECT"] - df["WAPP_CHURN"]

    return df

df = load_data()

# ==========================================================
# SIDEBAR FILTERS
# ==========================================================

st.sidebar.header("Filters")

# Date filter
min_date = df["WEEKLY_REVISED"].min()
max_date = df["WEEKLY_REVISED"].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Industry filter
industry_list = sorted(df["INDUSTRY"].unique())
selected_industries = st.sidebar.multiselect(
    "Select Industries",
    options=industry_list,
    default=industry_list
)

# Region filter
region_list = sorted(df["REGION"].unique())
selected_regions = st.sidebar.multiselect(
    "Select Regions",
    options=region_list,
    default=region_list
)

# Apply filters
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

col1.metric("Total Net WAPP", f"{int(df['NET_WAPP'].sum()):,}")
col2.metric("Total New WAPP", f"{int(df['WAPP_NEW'].sum()):,}")
col3.metric("Total Resurrect WAPP", f"{int(df['WAPP_RESURRECT'].sum()):,}")
col4.metric("Total Churn", f"{int(df['WAPP_CHURN'].sum()):,}")

st.markdown("---")

# ==========================================================
# TOP GROWTH INDUSTRIES
# ==========================================================

st.header("🟢 Top Industries for Sales Hiring")

sales = df.groupby("INDUSTRY").agg(
    Total_Net_WAPP=("NET_WAPP","sum"),
    Total_New_WAPP=("WAPP_NEW","sum"),
    Total_Resurrect_WAPP=("WAPP_RESURRECT","sum")
).reset_index().sort_values("Total_Net_WAPP", ascending=False)

st.dataframe(sales, use_container_width=True)

fig1 = px.bar(
    sales.head(10),
    x="INDUSTRY",
    y=["Total_New_WAPP", "Total_Resurrect_WAPP"],
    title="New vs Resurrect WAPP by Industry",
    barmode="group",
    color_discrete_sequence=["#6161FF", "#00CA72"]
)

st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# ==========================================================
# HIGH CHURN INDUSTRIES
# ==========================================================

st.header("🔴 High Churn Industries")

churn = df.groupby("INDUSTRY").agg(
    Avg_Churn=("WAPP_CHURN","mean"),
    Avg_Resurrect=("WAPP_RESURRECT","mean")
).reset_index().sort_values("Avg_Churn", ascending=False)

st.dataframe(churn.head(10), use_container_width=True)

fig2 = px.bar(
    churn.head(10),
    x="INDUSTRY",
    y=["Avg_Churn", "Avg_Resurrect"],
    title="Churn vs Resurrect Comparison",
    barmode="group",
    color_discrete_sequence=["#FB275D", "#6161FF"]
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ==========================================================
# WEEKLY TREND
# ==========================================================

st.header("📈 Weekly Trend (Revised Week)")

weekly = df.groupby("WEEKLY_REVISED").agg(
    Net_WAPP=("NET_WAPP","sum"),
    New_WAPP=("WAPP_NEW","sum"),
    Resurrect_WAPP=("WAPP_RESURRECT","sum")
).reset_index()

fig3 = px.line(
    weekly,
    x="WEEKLY_REVISED",
    y=["Net_WAPP", "New_WAPP", "Resurrect_WAPP"],
    title="Weekly Net, New & Resurrect WAPP",
    color_discrete_sequence=["#00CA72", "#6161FF", "#FFCC00"]
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ==========================================================
# REGIONAL BREAKDOWN
# ==========================================================

st.header("🌍 Regional Net WAPP")

regional = df.groupby("REGION")["NET_WAPP"].sum().reset_index()

fig4 = px.bar(
    regional,
    x="REGION",
    y="NET_WAPP",
    title="Net WAPP by Region",
    color_discrete_sequence=["#FFCC00"]
)

st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.markdown("Built for CRO strategic hiring • Global & Regional Allocation • monday.com Executives")

