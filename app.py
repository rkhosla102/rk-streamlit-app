import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="monday.com CRO Revenue Command Center", layout="wide")

# ==========================================================
# LOAD STRATEGIC WAPP DATA
# ==========================================================

@st.cache_data
def load_data():
    df = pd.read_csv("wapp_data.csv")
    df["WEEKLY_REVISED"] = pd.to_datetime(df["WEEKLY_REVISED"], errors="coerce")

    numeric_cols = ["WAPP_NEW", "WAPP_RESURRECT", "WAPP_CHURN", "WAPP"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["INDUSTRY"] = df["INDUSTRY"].astype(str)
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
    value=(min_date, max_date)
)

industries = sorted(df["INDUSTRY"].unique())
regions = sorted(df["REGION"].unique())

selected_industries = st.sidebar.multiselect("Industries", industries, default=industries)
selected_regions = st.sidebar.multiselect("Regions", regions, default=regions)

df = df[
    (df["WEEKLY_REVISED"] >= pd.Timestamp(date_range[0])) &
    (df["WEEKLY_REVISED"] <= pd.Timestamp(date_range[1])) &
    (df["INDUSTRY"].isin(selected_industries)) &
    (df["REGION"].isin(selected_regions))
]

# ==========================================================
# STRATEGIC WAPP SECTION
# ==========================================================

st.title("📊 CRO Strategic + Tactical Revenue Command Center")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Net WAPP", f"{int(df['NET_WAPP'].sum()):,}")
col2.metric("New WAPP", f"{int(df['WAPP_NEW'].sum()):,}")
col3.metric("Resurrect WAPP", f"{int(df['WAPP_RESURRECT'].sum()):,}")
col4.metric("Churn WAPP", f"{int(df['WAPP_CHURN'].sum()):,}")

st.markdown("---")

industry = df.groupby("INDUSTRY").agg(
    New=("WAPP_NEW","sum"),
    Resurrect=("WAPP_RESURRECT","sum"),
    Churn=("WAPP_CHURN","sum"),
    Net=("NET_WAPP","sum")
).reset_index().sort_values("Net", ascending=False)

fig_strategic = px.bar(
    industry.head(10),
    x="INDUSTRY",
    y=["New","Resurrect","Churn"],
    barmode="group",
    title="Strategic WAPP Breakdown"
)
st.plotly_chart(fig_strategic, use_container_width=True)

st.markdown("-------------------------------------------------------------------")

# ==========================================================
# 🎯 SALES HIRING → REVENUE IMPACT DASHBOARD
# ==========================================================

st.header("🎯 Sales Hiring → Revenue Impact Dashboard")

# --- Executive Summary (Mock Data)

Q1_goal_AE = 85
current_AE = 68
pipeline_AE = 12
shortage_AE = Q1_goal_AE - (current_AE + pipeline_AE)
ARR_per_AE = 800000
revenue_gap = shortage_AE * ARR_per_AE * 0.5  # assume partial ramp

col1, col2, col3, col4 = st.columns(4)

col1.metric("Q1 AE Goal", "85")
col2.metric("Current AEs", "68")
col3.metric("In Pipeline", "12")
col4.metric("Revenue Gap", f"${revenue_gap/1_000_000:.1f}M")

st.markdown("**Total Revenue At Risk:** $2.9M ARR")
st.markdown("**Time to Close Gap:** 8 weeks at current velocity")

st.markdown("---")

# ==========================================================
# FUNNEL VIEW (Mock)
# ==========================================================

st.subheader("Funnel View — Project Management AEs")

funnel_data = pd.DataFrame({
    "Stage": [
        "Sourcing",
        "Phone Screen",
        "Hiring Manager",
        "Final Round",
        "Offer Extended",
        "Offer Accepted"
    ],
    "Count": [45, 30, 24, 18, 12, 10]
})

fig_funnel = px.bar(
    funnel_data,
    x="Stage",
    y="Count",
    title="Hiring Funnel — PM AEs"
)

st.plotly_chart(fig_funnel, use_container_width=True)

st.markdown("⚠️ Bottleneck: Sourcing conversion below 75% target")

st.markdown("---")

# ==========================================================
# TIME TO PRODUCTIVITY
# ==========================================================

st.subheader("Ramp to Productivity — Q4 2025 AE Cohort")

months = ["M1","M2","M3","M4","M5","M6"]
target = [0,20,40,60,80,100]
actual = [0,18,35,52,68,80]

ramp_df = pd.DataFrame({
    "Month": months,
    "Target Ramp %": target,
    "Actual Ramp %": actual
})

fig_ramp = px.line(
    ramp_df,
    x="Month",
    y=["Target Ramp %","Actual Ramp %"],
    title="Ramp vs Target"
)

st.plotly_chart(fig_ramp, use_container_width=True)

st.markdown("⚠️ Ramp 12% behind benchmark — onboarding gap suspected")

st.markdown("---")

# ==========================================================
# SCENARIO PLANNING
# ==========================================================

st.subheader("Scenario Planning — Revenue Impact Simulator")

hires_per_month = st.slider("AEs Hired per Month", 2, 12, 6)
quota = 800000
attainment = st.slider("Quota Attainment %", 50, 100, 68)

ARR_impact = hires_per_month * quota * (attainment/100)

st.metric("Projected Annual ARR Impact", f"${ARR_impact/1_000_000:.1f}M")

st.markdown("---")

# ==========================================================
# BOTTLENECK ANALYSIS (Mock)
# ==========================================================

st.subheader("Top Bottlenecks Slowing Revenue")

st.markdown("""
🔴 **Sourcing Capacity (PM AEs)**  
→ 2.6:1 pipeline ratio (target 5:1)  
→ $3.8M ARR at risk  

🟡 **Final Round Scheduling Delays**  
→ 10 days vs 5 day benchmark  

🟡 **APAC Offer Acceptance (75%)**  
→ 10% below NA benchmark  
""")

st.markdown("---")

# ==========================================================
# QUALITY VS SPEED
# ==========================================================

st.subheader("Hiring Quality vs Speed")

quality_df = pd.DataFrame({
    "Cohort":["Q1 2025","Q2 2025","Q3 2025","Q4 2025"],
    "Time_to_Hire":[42,38,51,45],
    "Retention_90d":[92,87,78,90],
    "Quota_%":[74,68,62,70]
})

fig_quality = px.scatter(
    quality_df,
    x="Time_to_Hire",
    y="Quota_%",
    size="Retention_90d",
    color="Cohort",
    title="Hiring Speed vs Quota Performance"
)

st.plotly_chart(fig_quality, use_container_width=True)

st.markdown("---")

st.markdown("🔴 Critical: AE shortage in PM vertical → $2.1M ARR at risk")
st.markdown("🟡 High Priority: Ramp lagging 12%")
st.markdown("🟢 Wins: SDR hiring on track")


