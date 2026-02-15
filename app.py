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

if df_filtered.empty:
    st.warning("No data for selected filters.")
    st.stop()

# ==========================================================
# TITLE
# ==========================================================

st.title("📊 CRO Strategic + Tactical Revenue Command Center")

# ==========================================================
# STRATEGIC WAPP SUMMARY
# ==========================================================

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

# ==========================================================
# INDUSTRY BREAKDOWN
# ==========================================================

industry_summary = df_filtered.groupby("INDUSTRY").agg(
    New=("WAPP_NEW","sum"),
    Resurrect=("WAPP_RESURRECT","sum"),
    Churn=("WAPP_CHURN","sum"),
    Net=("NET_WAPP","sum")
).reset_index()

fig_industry = px.bar(
    industry_summary.sort_values("Net", ascending=False).head(10),
    x="INDUSTRY",
    y=["New","Resurrect","Churn"],
    barmode="group",
    title="Top Industries — WAPP Breakdown"
)

st.plotly_chart(fig_industry, use_container_width=True)

st.markdown("---")

# ==========================================================
# INDUSTRY INTELLIGENCE ENGINE
# ==========================================================

st.header("🧠 Industry Prioritization Engine")

industry_diag = industry_summary.copy()

industry_diag["WER"] = (
    (industry_diag["New"] + industry_diag["Resurrect"]) /
    industry_diag["Churn"].replace(0, np.nan)
)

industry_diag["Resurrection_Dependency"] = (
    industry_diag["Resurrect"] /
    (industry_diag["New"] + industry_diag["Resurrect"]).replace(0, np.nan)
)

industry_diag["New_to_Churn_Ratio"] = (
    industry_diag["New"] /
    industry_diag["Churn"].replace(0, np.nan)
)

weeks_in_period = max(
    1,
    (df_filtered["WEEKLY_REVISED"].max() - df_filtered["WEEKLY_REVISED"].min()).days / 7
)

industry_diag["Churn_Velocity"] = industry_diag["Churn"] / weeks_in_period

industry_diag = industry_diag.replace([np.inf, -np.inf], np.nan).fillna(0)

def classify(row):
    if row["WER"] < 1 and row["Churn_Velocity"] > industry_diag["Churn_Velocity"].median():
        return "🔴 Fix Churn"
    elif row["WER"] > 1.2 and row["Resurrection_Dependency"] < 0.4:
        return "🟢 Accelerate AE Hiring"
    elif row["Resurrection_Dependency"] > 0.7:
        return "🟡 Fragile Growth"
    elif row["New_to_Churn_Ratio"] > 1.5:
        return "🟢 SDR Expansion"
    else:
        return "⚪ Monitor"

industry_diag["Strategic_Action"] = industry_diag.apply(classify, axis=1)
industry_diag["Opportunity_Score"] = (
    industry_diag["Net"] * industry_diag["WER"]
).abs()

industry_diag = industry_diag.sort_values("Opportunity_Score", ascending=False)

st.dataframe(industry_diag.round(2), use_container_width=True)

fig_auto = px.scatter(
    industry_diag,
    x="Churn_Velocity",
    y="WER",
    size="Opportunity_Score",
    color="Strategic_Action",
    hover_name="INDUSTRY",
    size_max=60
)

fig_auto.add_hline(y=1, line_dash="dash")
st.plotly_chart(fig_auto, use_container_width=True)

# ==========================================================
# EXECUTIVE ALERTS
# ==========================================================

st.subheader("🚨 Executive Alerts")

critical = industry_diag[industry_diag["Strategic_Action"] == "🔴 Fix Churn"]
growth = industry_diag[industry_diag["Strategic_Action"] == "🟢 Accelerate AE Hiring"]

if not critical.empty:
    st.error(f"High Churn Risk: {', '.join(critical['INDUSTRY'].head(3))}")

if not growth.empty:
    st.success(f"Scale Sales Hiring In: {', '.join(growth['INDUSTRY'].head(3))}")

st.markdown("---")

# ==========================================================
# REVENUE MODELING
# ==========================================================

st.header("🎯 Sales Hiring → Revenue Impact")

st.sidebar.header("Hiring Controls")

role = st.sidebar.selectbox(
    "Role Type",
    ["Account Executives", "SDRs", "CSMs"]
)

quarter_goal = st.sidebar.number_input("Quarter Hiring Goal", 1, value=20)
current_headcount = st.sidebar.number_input("Current Active Headcount", 0, value=15)
pipeline_count = st.sidebar.number_input("Candidates in Pipeline", 0, value=8)
quota_attainment = st.sidebar.slider("Quota Attainment %", 50, 100, 70)
ramp_months = st.sidebar.slider("Ramp Time (months)", 3, 9, 6)

BASE_AE_QUOTA = 750000

ROLE_MULTIPLIER = {
    "Account Executives": 1.0,
    "SDRs": 0.25,
    "CSMs": 0.4
}

arr_quota = BASE_AE_QUOTA * ROLE_MULTIPLIER[role]

growth_scaler = max(0.1, total_net / max(1, df["NET_WAPP"].sum()))
scaled_quota = arr_quota * growth_scaler

ramp_factor = min(1.0, ramp_months / 6)
effective_arr_per_rep = scaled_quota * (quota_attainment / 100) * ramp_factor

existing_arr = current_headcount * effective_arr_per_rep
expected_new_hires = int(pipeline_count * 0.5)
pipeline_arr = expected_new_hires * effective_arr_per_rep

required_arr = quarter_goal * effective_arr_per_rep
arr_gap = max(0, required_arr - (existing_arr + pipeline_arr))

col1, col2, col3, col4 = st.columns(4)

col1.metric("ARR Capacity", f"${existing_arr + pipeline_arr:,.0f}")
col2.metric("ARR Required", f"${required_arr:,.0f}")
col3.metric("Revenue at Risk", f"${arr_gap:,.0f}")
col4.metric("Effective ARR / Rep", f"${effective_arr_per_rep:,.0f}")

st.markdown("---")

# ==========================================================
# FUNNEL SIMULATION
# ==========================================================

st.subheader("📊 Hiring Funnel")

stages = ["Sourcing","Phone Screen","Hiring Manager","Final Round","Offer","Accepted"]
drop_rates = [1, 0.7, 0.8, 0.75, 0.8, 0.85]

counts = []
base = max(pipeline_count * 3, 1)

for rate in drop_rates:
    base = int(base * rate)
    counts.append(base)

funnel_df = pd.DataFrame({"Stage": stages, "Candidates": counts})

st.plotly_chart(
    px.bar(funnel_df, x="Stage", y="Candidates"),
    use_container_width=True
)

st.markdown("---")

# ==========================================================
# RAMP MODEL
# ==========================================================

st.subheader("⏱ Ramp to Productivity")

months = list(range(1, ramp_months + 1))
target_ramp = np.linspace(0, 100, ramp_months)
actual_ramp = target_ramp * (quota_attainment / 100)

ramp_df = pd.DataFrame({
    "Month": months,
    "Target": target_ramp,
    "Actual": actual_ramp
})

st.plotly_chart(
    px.line(ramp_df, x="Month", y=["Target","Actual"], markers=True),
    use_container_width=True
)

st.markdown("---")

# ==========================================================
# SCENARIO SIMULATOR
# ==========================================================

st.subheader("🧮 Scenario Simulator")

hires_per_month = st.slider("Hires per Month", 1, 15, 5)
projected_arr = hires_per_month * effective_arr_per_rep

st.metric("Projected ARR Impact", f"${projected_arr:,.0f}")

st.success("Strategic + Tactical CRO command center fully active.")
