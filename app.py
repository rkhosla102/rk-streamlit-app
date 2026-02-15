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
# BRAND STYLING (monday.com inspired)
# ==========================================================

st.markdown("""
<style>
    body { background-color: #F5F6F8; }
    .main-title {
        font-size: 34px;
        font-weight: 700;
        color: #6161FF;
    }
    .sub-title {
        font-size: 18px;
        color: #181B34;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 monday.com CRO Strategic Hiring Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Global hiring & growth intelligence using Revised Weekly WAPP</div>', unsafe_allow_html=True)

st.markdown("---")

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

    # Clean Industry + Region
    df["INDUSTRY"] = df["INDUSTRY"].astype(str)
    df["REGION"] = df["REGION"].astype(str)

    df = df[df["INDUSTRY"].str.strip() != ""]
    df = df[df["REGION"].str.strip() != ""]

    # Create Net WAPP
    df["NET_WAPP"] = df["WAPP_NEW"] + df["WAPP_RESURRECT"] - df["WAPP_CHURN"]

    return df

df = load_data()

# ==========================================================
# SIDEBAR FILTERS
# ==========================================================

st.sidebar.header("Filters")

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
    (df["INDUSTRY"].isin(selected_industries)) &
    (df["REGION"].isin(selected_regions))
]

# ==========================================================
# EXECUTIVE KPIs
# ==========================================================

st.header("Executive Snapshot")

col1, col2, col3 = st.columns(3)

total_net = df["NET_WAPP"].sum()
total_new = df["WAPP_NEW"].sum()
total_churn = df["WAPP_CHURN"].sum()

col1.metric("Total Net WAPP", f"{int(total_net):,}")
col2.metric("Total New WAPP", f"{int(total_new):,}")
col3.metric("Total Churn", f"{int(total_churn):,}")

st.markdown("---")

# ==========================================================
# TOP GROWTH INDUSTRIES
# ==========================================================

st.header("🟢 Top Industries for Sales Hiring")

sales = df.groupby("INDUSTRY").agg(
    Total_Net_WAPP=("NET_WAPP","sum"),
    Avg_Weekly_Net_WAPP=("NET_WAPP","mean"),
    Avg_New_WAPP=("WAPP_NEW","mean")
).reset_index().sort_values("Total_Net_WAPP", ascending=False)

st.dataframe(sales, use_container_width=True)

fig1 = px.bar(
    sales.head(10),
    x="INDUSTRY",
    y="Total_Net_WAPP",
    title="Top Industries by Net WAPP Growth",
    color_discrete_sequence=["#6161FF"]
)

st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# ==========================================================
# HIGH CHURN INDUSTRIES
# ==========================================================

st.header("🔴 High Churn Industries (CS Hiring Priority)")

churn = df.groupby("INDUSTRY").agg(
    Avg_Churn=("WAPP_CHURN","mean"),
    Avg_Resurrect=("WAPP_RESURRECT","mean")
).reset_index()

churn["Resurrection_Dependency"] = (
    churn["Avg_Resurrect"] /
    (churn["Avg_Resurrect"] + churn["Avg_Churn"]).replace(0,1)
)

churn = churn.sort_values("Avg_Churn", ascending=False)

st.dataframe(churn.head(10), use_container_width=True)

fig2 = px.bar(
    churn.head(10),
    x="INDUSTRY",
    y="Avg_Churn",
    title="Highest Churn Segments",
    color_discrete_sequence=["#FB275D"]
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ==========================================================
# EMERGING INDUSTRIES
# ==========================================================

st.header("🌱 Emerging Industries")

first_seen = df.groupby("INDUSTRY")["WEEKLY_REVISED"].min().reset_index()
first_seen = first_seen.sort_values("WEEKLY_REVISED", ascending=False)

st.dataframe(first_seen.head(10), use_container_width=True)

st.markdown("---")

# ==========================================================
# WEEKLY TREND
# ==========================================================

st.header("📈 Weekly Net WAPP Trend (Revised Week)")

weekly = df.groupby("WEEKLY_REVISED")["NET_WAPP"].sum().reset_index()

fig3 = px.line(
    weekly,
    x="WEEKLY_REVISED",
    y="NET_WAPP",
    title="Total Weekly Net WAPP",
    color_discrete_sequence=["#00CA72"]
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ==========================================================
# REGIONAL BREAKDOWN
# ==========================================================

st.header("🌍 Regional Performance")

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

# ==========================================================
# CRO STRATEGIC SUMMARY
# ==========================================================

st.header("💡 CRO Strategic Recommendations")

st.markdown("""
**1️⃣ Hire AEs** → Highest Net WAPP industries  
**2️⃣ Hire CSMs** → High churn verticals  
**3️⃣ Prospect Emerging Segments** → New vertical growth  
**4️⃣ Push Annual Contracts** → Stable industries  
**5️⃣ Optimize Global Allocation** → Use region filter for territory hiring  
""")

st.markdown("---")
st.markdown("monday.com-inspired dashboard • Transparency • Customer-Centric • Execution-Focused")
