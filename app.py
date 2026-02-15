import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="monday.com CRO Revenue Command Center",
    layout="wide"
)

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

    df["INDUSTRY"] = df["INDUSTRY"].astype(str).replace("nan", "Unknown")
    df["REGION"] = df["REGION"].fillna("NA").replace("nan", "NA").astype(str)

    df["NET_WAPP"] = df["WAPP_NEW"] + df["WAPP_RESURRECT"] - df["WAPP_CHURN"]

    return df

df = load_data()

# ==========================================================
# SIDEBAR FILTERS
# ==========================================================

st.sidebar.header("Strategic Filters")

min_date = df["WEEKLY_REVISED"].min()
max_date = df["WEEKLY_REVISED"].max()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date)
)

industries = sorted(df["INDUSTRY"].unique())
regions = sorted(df["REGION"].unique())

selected_industries = st.sidebar.multiselect(
    "Industries",
    industries,
    default=industries
)

selected_regions = st.sidebar.multiselect(
    "Regions",
    regions,
    default=regions
)

df_filtered = df[
    (df["WEEKLY_REVISED"] >= pd.Timestamp(date_range[0])) &
    (df["WEEKLY_REVISED"] <= pd.Timestamp(date_range[1])) &
    (df["INDUSTRY"].isin(selected_industries)) &
    (df["REGION"].isin(selected_regions))
]

# ==========================================================
# STRATEGIC SECTION
# ==========================================================

st.title("📊 CRO Strategic + Tactical Revenue Command Center")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Net WAPP", f"{int(df_filtered['NET_WAPP'].sum()):,}")
col2.metric("New WAPP", f"{int(df_filtered['WAPP_NEW'].sum()):,}")
col3.metric("Resurrect WAPP", f"{int(df_filtered['WAPP_RESURRECT'].sum()):,}")
col4.metric("Churn WAPP", f"{int(df_filtered['WAPP_CHURN'].sum()):,}")

st.markdown("---")

industry_summary = df_filtered.groupby("INDUSTRY").agg(
    New=("WAPP_NEW","sum"),
    Resurrect=("WAPP_RESURRECT","sum"),
    Churn=("WAPP_CHURN","sum"),
    Net=("NET_WAPP","sum")
).reset_index().sort_values("Net", ascending=False)

fig_industry = px.bar(
    industry_summary.head(10),
    x="INDUSTRY",
    y=["New","Resurrect","Churn"],
    barmode="group",
    title="Top Industries — WAPP Breakdown"
)

st.plotly_chart(fig_industry, use_container_width=True)

st.markdown("---")

# ==========================================================
# TACTICAL LAYER
# ==========================================================

st.header("🎯 Sales Hiring → Revenue Impact")

st.sidebar.header("Hiring Scenario Controls")

role = st.sidebar.selectbox(
    "Role Type",
    ["Account Executives", "SDRs", "CSMs"]
)

quarter_goal = st.sidebar.number_input("Quarter Hiring Goal", min_value=1, value=20)
current_headcount = st.sidebar.number_input("Current Active Headcount", min_value=0, value=15)
pipeline_count = st.sidebar.number_input("Candidates in Pipeline", min_value=0, value=8)

avg_quota = st.sidebar.number_input("Avg Annual Quota ($)", value=800000)
quota_attainment = st.sidebar.slider("Quota Attainment %", 50, 100, 70)
ramp_months = st.sidebar.slider("Ramp Time (months)", 3, 9, 6)

# ==========================================================
# EXECUTIVE SUMMARY — REVENUE GAP
# ==========================================================

hires_gap = max(0, quarter_goal - (current_headcount + pipeline_count))
revenue_per_role = avg_quota * (quota_attainment / 100)
revenue_at_risk = hires_gap * revenue_per_role * (ramp_months / 12)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Quarter Goal", quarter_goal)
col2.metric("Active", current_headcount)
col3.metric("Pipeline", pipeline_count)
col4.metric("Revenue at Risk", f"${revenue_at_risk/1_000_000:.2f}M")

st.markdown("---")

# ==========================================================
# FUNNEL SIMULATION
# ==========================================================

st.subheader("📊 Hiring Funnel Simulation")

stage_names = [
    "Sourcing",
    "Phone Screen",
    "Hiring Manager",
    "Final Round",
    "Offer Extended",
    "Offer Accepted"
]

drop_rates = [1, 0.7, 0.8, 0.75, 0.8, 0.85]

counts = []
base = max(pipeline_count * 3, 1)

for rate in drop_rates:
    base = int(base * rate)
    counts.append(base)

funnel_df = pd.DataFrame({
    "Stage": stage_names,
    "Candidates": counts
})

fig_funnel = px.bar(
    funnel_df,
    x="Stage",
    y="Candidates",
    title=f"{role} Funnel"
)

st.plotly_chart(fig_funnel, use_container_width=True)

st.markdown("---")

# ==========================================================
# RAMP MODEL
# ==========================================================

st.subheader("⏱ Time to Productivity")

months = list(range(1, ramp_months + 1))
target_ramp = np.linspace(0, 100, ramp_months)
actual_ramp = target_ramp * (quota_attainment / 100)

ramp_df = pd.DataFrame({
    "Month": months,
    "Target Ramp %": target_ramp,
    "Actual Ramp %": actual_ramp
})

fig_ramp = px.line(
    ramp_df,
    x="Month",
    y=["Target Ramp %","Actual Ramp %"],
    markers=True
)

st.plotly_chart(fig_ramp, use_container_width=True)

st.markdown("---")

# ==========================================================
# SCENARIO PLANNER
# ==========================================================

st.subheader("🧮 Scenario Planner")

hires_per_month = st.slider("Hires per Month", 1, 15, 5)
time_to_hire = st.slider("Time to Hire (Days)", 20, 90, 45)

projected_arr = hires_per_month * revenue_per_role

col1, col2 = st.columns(2)
col1.metric("Projected Annual ARR Impact", f"${projected_arr/1_000_000:.2f}M")
col2.metric("Time to Hire", f"{time_to_hire} days")

st.markdown("---")

# ==========================================================
# QUALITY VS SPEED VISUAL
# ==========================================================

st.subheader("📈 Hiring Speed vs Revenue Output")

quality_df = pd.DataFrame({
    "Time_to_Hire":[35,45,55,60],
    "Quota_Attainment":[75,70,62,58],
    "Cohort":["Fast","Moderate","Slow","Very Slow"]
})

fig_quality = px.scatter(
    quality_df,
    x="Time_to_Hire",
    y="Quota_Attainment",
    size="Quota_Attainment",
    color="Cohort"
)

st.plotly_chart(fig_quality, use_container_width=True)

st.markdown("---")

st.success("Dashboard ready for CRO scenario planning.")
