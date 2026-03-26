import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Marketing Campaign Performance Dashboard",
    page_icon="📈",
    layout="wide"
)

# ---------- Helpers ----------
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_excel("Campaign Dataset Big.xlsx")

    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]

    required_cols = [
        "Campaign_ID", "Channel", "Region", "Budget",
        "Leads_Generated", "Conversions", "Revenue"
    ]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        st.stop()

    # Numeric conversion
    numeric_cols = ["Budget", "Leads_Generated", "Conversions", "Revenue"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Recalculate metrics safely
    df["Conversion_Rate"] = (df["Conversions"] / df["Leads_Generated"]).fillna(0)
    df["ROI"] = ((df["Revenue"] - df["Budget"]) / df["Budget"]).fillna(0)

    df = df.dropna(subset=["Campaign_ID", "Channel", "Region"])
    return df


def indian_currency(x):
    return f"₹{x:,.0f}"


# ---------- Data ----------
st.title("📊 B2B Marketing Campaign Performance Dashboard")
st.markdown("Track campaign effectiveness using KPIs, filters, and visual analytics.")

with st.sidebar:
    st.header("Dashboard Controls")
    uploaded_file = st.file_uploader(
        "Upload campaign dataset (Excel or CSV)",
        type=["xlsx", "xls", "csv"]
    )

df = load_data(uploaded_file)

# ---------- Filters ----------
with st.sidebar:
    channels = st.multiselect(
        "Select Channel",
        sorted(df["Channel"].dropna().unique()),
        default=sorted(df["Channel"].dropna().unique())
    )

    regions = st.multiselect(
        "Select Region",
        sorted(df["Region"].dropna().unique()),
        default=sorted(df["Region"].dropna().unique())
    )

filtered_df = df[
    df["Channel"].isin(channels) &
    df["Region"].isin(regions)
].copy()

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ---------- KPI Calculations ----------
total_campaigns = filtered_df["Campaign_ID"].nunique()
total_revenue = filtered_df["Revenue"].sum()
total_budget = filtered_df["Budget"].sum()
overall_conversion_rate = (
    filtered_df["Conversions"].sum() / filtered_df["Leads_Generated"].sum()
    if filtered_df["Leads_Generated"].sum() > 0 else 0
)
overall_roi = (
    (total_revenue - total_budget) / total_budget
    if total_budget > 0 else 0
)

# ---------- KPI Cards ----------
st.subheader("Key Performance Indicators")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Campaigns", f"{total_campaigns}")
k2.metric("Conversion Rate", f"{overall_conversion_rate:.2%}")
k3.metric("ROI", f"{overall_roi:.2%}")
k4.metric("Revenue", indian_currency(total_revenue))

st.markdown("---")

# ---------- Charts ----------
left, right = st.columns(2)

with left:
    st.subheader("Channel Performance")
    channel_perf = (
        filtered_df.groupby("Channel", as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Conversions=("Conversions", "sum"),
            Budget=("Budget", "sum"),
            Campaigns=("Campaign_ID", "nunique")
        )
        .sort_values("Revenue", ascending=False)
    )

    fig_channel = px.bar(
        channel_perf,
        x="Channel",
        y="Revenue",
        text="Revenue",
        hover_data=["Conversions", "Budget", "Campaigns"],
        title="Revenue by Channel"
    )
    fig_channel.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig_channel.update_layout(height=430, xaxis_title="Channel", yaxis_title="Revenue")
    st.plotly_chart(fig_channel, use_container_width=True)

with right:
    st.subheader("Conversion Rate by Region")
    region_perf = (
        filtered_df.groupby("Region", as_index=False)
        .agg(
            Leads_Generated=("Leads_Generated", "sum"),
            Conversions=("Conversions", "sum")
        )
    )
    region_perf["Conversion_Rate"] = (
        region_perf["Conversions"] / region_perf["Leads_Generated"]
    ).fillna(0)
    region_perf = region_perf.sort_values("Conversion_Rate", ascending=False)

    fig_region = px.bar(
        region_perf,
        x="Region",
        y="Conversion_Rate",
        text=region_perf["Conversion_Rate"].map(lambda x: f"{x:.2%}"),
        hover_data=["Leads_Generated", "Conversions"],
        title="Regional Conversion Efficiency"
    )
    fig_region.update_traces(textposition="outside")
    fig_region.update_layout(
        height=430,
        xaxis_title="Region",
        yaxis_title="Conversion Rate",
        yaxis_tickformat=".0%"
    )
    st.plotly_chart(fig_region, use_container_width=True)

st.subheader("Budget vs Revenue")
fig_scatter = px.scatter(
    filtered_df,
    x="Budget",
    y="Revenue",
    color="Channel",
    size="Conversions",
    hover_data=["Campaign_ID", "Region", "Leads_Generated", "Conversion_Rate", "ROI"],
    title="Budget vs Revenue by Campaign"
)
fig_scatter.update_layout(height=500, xaxis_title="Budget", yaxis_title="Revenue")
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# ---------- Top Insights ----------
st.subheader("Quick Business Insights")

best_channel_row = channel_perf.iloc[0]
best_roi_campaign = filtered_df.sort_values("ROI", ascending=False).iloc[0]
budget_efficiency = total_revenue / total_budget if total_budget > 0 else 0

c1, c2, c3 = st.columns(3)
c1.info(
    f"**Best Performing Channel:** {best_channel_row['Channel']}  \n"
    f"Revenue generated: {indian_currency(best_channel_row['Revenue'])}"
)
c2.success(
    f"**Highest ROI Campaign:** {best_roi_campaign['Campaign_ID']}  \n"
    f"ROI: {best_roi_campaign['ROI']:.2%}"
)
c3.warning(
    f"**Budget Utilization:** For every ₹1 spent, the campaigns generated "
    f"₹{budget_efficiency:.2f} in revenue."
)

# ---------- Data Preview ----------
with st.expander("View Campaign Data"):
    display_df = filtered_df.copy()
    display_df["Conversion_Rate"] = display_df["Conversion_Rate"].map(lambda x: f"{x:.2%}")
    display_df["ROI"] = display_df["ROI"].map(lambda x: f"{x:.2%}")
    st.dataframe(display_df, use_container_width=True)

# ---------- Footer ----------
st.caption("Built with Streamlit for B2B Marketing Campaign Automation and Performance Analytics")
