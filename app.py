import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="B2B Marketing Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------- Custom Styling ----------
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fc;
    }
    .title-text {
        font-size: 36px;
        font-weight: 700;
        color: #1f4e79;
        margin-bottom: 5px;
    }
    .sub-text {
        font-size: 16px;
        color: #555;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 6px solid #1f77b4;
    }
    .kpi-title {
        font-size: 16px;
        color: #666;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: bold;
        color: #111;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Load Data ----------
@st.cache_data
def load_data():
    df = pd.read_excel("Campaign_Data_15_Final.xlsx")
    df.columns = [col.strip() for col in df.columns]

    # Convert numeric columns
    numeric_cols = ["Budget", "Leads_Generated", "Conversions", "Revenue"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derived metrics
    df["Conversion_Rate"] = (df["Conversions"] / df["Leads_Generated"]).fillna(0)
    df["ROI"] = ((df["Revenue"] - df["Budget"]) / df["Budget"]).fillna(0)

    return df

df = load_data()

# ---------- Header ----------
st.markdown('<div class="title-text">📊 B2B Marketing Campaign Performance Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-text">Analyze campaign success using KPIs, filters, and interactive visualizations.</div>',
    unsafe_allow_html=True
)

# ---------- Sidebar ----------
st.sidebar.title("🔍 Dashboard Filters")

channel_filter = st.sidebar.multiselect(
    "Select Channel",
    options=sorted(df["Channel"].dropna().unique()),
    default=sorted(df["Channel"].dropna().unique())
)

region_filter = st.sidebar.multiselect(
    "Select Region",
    options=sorted(df["Region"].dropna().unique()),
    default=sorted(df["Region"].dropna().unique())
)

filtered_df = df[
    (df["Channel"].isin(channel_filter)) &
    (df["Region"].isin(region_filter))
]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# ---------- KPI Calculations ----------
total_campaigns = filtered_df["Campaign_ID"].nunique()
total_revenue = filtered_df["Revenue"].sum()
total_budget = filtered_df["Budget"].sum()
total_leads = filtered_df["Leads_Generated"].sum()
total_conversions = filtered_df["Conversions"].sum()

overall_conversion_rate = total_conversions / total_leads if total_leads > 0 else 0
overall_roi = (total_revenue - total_budget) / total_budget if total_budget > 0 else 0

# ---------- KPI Cards ----------
st.subheader("📌 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Campaigns</div>
            <div class="kpi-value">{total_campaigns}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Conversion Rate</div>
            <div class="kpi-value">{overall_conversion_rate:.2%}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">ROI</div>
            <div class="kpi-value">{overall_roi:.2%}</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Revenue</div>
            <div class="kpi-value">₹{total_revenue:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------- Chart 1: Channel Performance ----------
channel_perf = (
    filtered_df.groupby("Channel", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Conversions=("Conversions", "sum"),
        Leads=("Leads_Generated", "sum"),
        Budget=("Budget", "sum")
    )
    .sort_values("Revenue", ascending=False)
)

# ---------- Chart 2: Conversion Rate by Region ----------
region_perf = (
    filtered_df.groupby("Region", as_index=False)
    .agg(
        Leads=("Leads_Generated", "sum"),
        Conversions=("Conversions", "sum")
    )
)

region_perf["Conversion_Rate"] = (region_perf["Conversions"] / region_perf["Leads"]).fillna(0)
region_perf = region_perf.sort_values("Conversion_Rate", ascending=False)

col5, col6 = st.columns(2)

with col5:
    fig_channel = px.bar(
        channel_perf,
        x="Channel",
        y="Revenue",
        color="Channel",
        text="Revenue",
        title="💰 Channel Performance"
    )
    fig_channel.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig_channel.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_title="Channel",
        yaxis_title="Revenue",
        showlegend=False,
        height=450
    )
    st.plotly_chart(fig_channel, use_container_width=True)

with col6:
    fig_region = px.bar(
        region_perf,
        x="Region",
        y="Conversion_Rate",
        color="Region",
        text=region_perf["Conversion_Rate"].map(lambda x: f"{x:.2%}"),
        title="📍 Conversion Rate by Region"
    )
    fig_region.update_traces(textposition="outside")
    fig_region.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_title="Region",
        yaxis_title="Conversion Rate",
        yaxis_tickformat=".0%",
        showlegend=False,
        height=450
    )
    st.plotly_chart(fig_region, use_container_width=True)

# ---------- Chart 3: Budget vs Revenue ----------
st.subheader("📈 Budget vs Revenue")

fig_scatter = px.scatter(
    filtered_df,
    x="Budget",
    y="Revenue",
    color="Channel",
    size="Conversions",
    hover_data=["Campaign_ID", "Region", "Leads_Generated", "Conversion_Rate", "ROI"],
    title="Budget Utilization Across Campaigns"
)
fig_scatter.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis_title="Budget",
    yaxis_title="Revenue",
    height=500
)
st.plotly_chart(fig_scatter, use_container_width=True)

# ---------- Optional Extra Chart ----------
st.subheader("🎯 Leads vs Conversions")

fig_leads = px.scatter(
    filtered_df,
    x="Leads_Generated",
    y="Conversions",
    color="Channel",
    size="Budget",
    hover_data=["Campaign_ID", "Region"],
    title="Lead Conversion Efficiency"
)
fig_leads.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis_title="Leads Generated",
    yaxis_title="Conversions",
    height=500
)
st.plotly_chart(fig_leads, use_container_width=True)

# ---------- Insights ----------
st.subheader("🧠 Business Insights")

best_channel = channel_perf.iloc[0]
best_roi_campaign = filtered_df.sort_values("ROI", ascending=False).iloc[0]
budget_efficiency = total_revenue / total_budget if total_budget > 0 else 0

ins1, ins2, ins3 = st.columns(3)

with ins1:
    st.info(
        f"**Best Performing Channel:** {best_channel['Channel']}\n\n"
        f"Generated highest revenue of **₹{best_channel['Revenue']:,.0f}**."
    )

with ins2:
    st.success(
        f"**Highest ROI Campaign:** {best_roi_campaign['Campaign_ID']}\n\n"
        f"ROI achieved: **{best_roi_campaign['ROI']:.2%}**."
    )

with ins3:
    st.warning(
        f"**Budget Utilization:**\n\n"
        f"For every **₹1 spent**, campaigns generated **₹{budget_efficiency:.2f}** in revenue."
    )

# ---------- Data Table ----------
st.subheader("📋 Campaign Data Preview")

display_df = filtered_df.copy()
display_df["Conversion_Rate"] = display_df["Conversion_Rate"].map(lambda x: f"{x:.2%}")
display_df["ROI"] = display_df["ROI"].map(lambda x: f"{x:.2%}")

st.dataframe(display_df, use_container_width=True)

# ---------- Footer ----------
st.markdown("---")
st.caption("Developed using Streamlit for B2B Marketing Campaign Automation and Performance Analytics")
