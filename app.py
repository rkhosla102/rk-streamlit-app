import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="CRO Hiring Tracker", layout="wide")

st.title("📋 CRO Hiring & Growth Dashboard")

@st.cache_data
def load_data():
    df = pd.read_csv("wapp_data.csv")
    df["WEEKLY_REVISED"] = pd.to_datetime(df["WEEKLY_REVISED"])
    df = df.fillna(0)
    df["NET_WAPP"] = df["WAPP_NEW"] + df["WAPP_RESURRECT"] - df["WAPP_CHURN"]
    return df

df = load_data()

st.sidebar.header("Filters")

industries = st.sidebar.multiselect(
    "Select Industries",
    options=sorted(df["INDUSTRY"].unique()),
    default=sorted(df["INDUSTRY"].unique())
)

df = df[df["INDUSTRY"].isin(industries)]

st.header("🟢 Top Industries for Sales Hiring")

sales = df.groupby("INDUSTRY").agg(
    Total_Net_WAPP=("NET_WAPP","sum"),
    Avg_Weekly_Net_WAPP=("NET_WAPP","mean"),
    Avg_New_WAPP=("WAPP_NEW","mean")
).reset_index().sort_values("Total_Net_WAPP", ascending=False)

st.dataframe(sales, use_container_width=True)

fig = px.bar(
    sales.head(10),
    x="INDUSTRY",
    y="Total_Net_WAPP",
    title="Top Industries by Net WAPP Growth"
)
st.plotly_chart(fig, use_container_width=True)

st.header("🔴 High Churn Industries")

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
    title="Highest Churn Segments"
)
st.plotly_chart(fig2, use_container_width=True)

st.header("🌱 Emerging Industries")

first_seen = df.groupby("INDUSTRY")["WEEKLY_REVISED"].min().reset_index()
first_seen = first_seen.sort_values("WEEKLY_REVISED", ascending=False)

st.dataframe(first_seen.head(10), use_container_width=True)

st.header("📈 Weekly Net WAPP Trend")

weekly = df.groupby("WEEKLY_REVISED")["NET_WAPP"].sum().reset_index()

fig3 = px.line(
    weekly,
    x="WEEKLY_REVISED",
    y="NET_WAPP",
    title="Total Weekly Net WAPP"
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.markdown("### 💡 CRO Bottom Line")
st.markdown("""
1. Hire AEs in highest Net WAPP industries  
2. Hire CSMs in high churn segments  
3. Prospect emerging verticals  
4. Push annual contracts in stable segments  
""")
