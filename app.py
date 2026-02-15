import streamlit as st
import pandas as pd
import plotly.express as px
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
# STRATEGIC SECTION — WAPP PERFORMANCE
# ==========================================================

st.title("📊 CRO Strategic + Tactical Revenue Command Center")

col1, col2, col3, col4 = st.columns(4)

total_net = df_filtered["NET_WAPP"].sum()
total_new = df_filtered["WAPP_NEW"].sum()
total_res = df_filtered["WAPP_RESURRECT"].sum()
total_churn = df_filtered["WAPP_CHURN"].sum()

col1.metric("Net WAPP", f"{int(total_net):,}")
col2.metric("New WAPP", f"{int(total_new):,}")
col3.metric("Resurrect WAPP", f"{int(total_res):,}")
col4.metric("Churn WAPP", f"{int(total_churn):,}")

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
# DATA-DRIVEN REVENUE MODELING
# ==========================================================

st.header("🎯 Sales Hiring → Revenue Impact (Data Driven)")

st.sidebar.header("Hiring Controls")

role = st.sidebar.selectbox(
    "Role Type",
    ["Account Executives", "SDRs", "CSMs"]
)

quarter_goal = st.sidebar.number_input("Quarter Hiring Goal", min_value=1, value=20)
current_headcount = st.sidebar.number_input("Current Active Headcount", min_value=0, value=15)
pipeline_count = st.sidebar.number_input("Candidates in Pipeline", min_value=0, value=8)
quota_attainment = st.sidebar.slider("Quota Attainment %", 50, 100, 70)
ramp_months = st.sidebar.slider("Ramp Time (months)", 3, 9, 6)

# ==========================================================
# REVENUE ASSUMPTIONS FROM DATA
# ==========================================================

# Use Net WAPP as proxy for demand capacity
demand_factor = max(1, total_net)

# Industry SaaS median quota benchmark
BASE_AE_QUOTA = 750000

ROLE_MULTIPLIER = {
    "Account Executives": 1.0,
    "SDRs": 0.25,
    "CSMs": 0.4
}

arr_quota = BASE_AE_QUOTA * ROLE_MULTIPLIER[role]

# scale ARR capacity based on filtered WAPP growth
growth_scaler = demand_factor / df["NET_WAPP"].sum()
scaled_quota = arr_quota * growth_scaler

# ramp adjustment
ramp_factor = min(1.0, ramp_months / 6)

effective_arr_per_rep = scaled_quota * (quota_attainment / 100) * ramp_factor

# ARR capacity
existing_arr = current_headcount * effective_arr_per_rep

pipeline_conversion_rate = 0.5
expected_new_hires = int(pipeline_count * pipeline_conversion_rate)
pipeline_arr = expected_new_hires * effective_arr_per_rep

required_arr = quarter_goal * effective_arr_per_rep

arr_gap = max(0, required_arr - (existing_arr + pipeline_arr))

# ==========================================================
# EXEC SUMMARY
# ==========================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric("ARR Capacity (Current + Pipeline)", f"${existing_arr + pipeline_arr:,.0f}")
col2.metric("ARR Required to Hit Goal", f"${required_arr:,.0f}")
col3.metric("Revenue at Risk", f"${arr_gap:,.0f}")
col4.metric("Effective ARR / Rep", f"${effective_arr_per_rep:,.0f}")

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
# RAMP VISUAL
# ==========================================================

st.subheader("⏱ Ramp to Productivity")

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
# SCENARIO SIMULATOR
# ==========================================================

st.subheader("🧮 Scenario Simulator")

hires_per_month = st.slider("Hires per Month", 1, 15, 5)
time_to_hire_days = st.slider("Time to Hire (Days)", 20, 90, 45)

projected_arr = hires_per_month * effective_arr_per_rep

col1, col2 = st.columns(2)
col1.metric("Projected Annual ARR Impact", f"${projected_arr:,.0f}")
col2.metric("Time to Hire", f"{time_to_hire_days} days")

st.markdown("---")

st.success("Revenue modeling tied dynamically to WAPP demand + hiring inputs.")
