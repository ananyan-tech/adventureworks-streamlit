"""AdventureWorks Operations Command Center."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import database_name, load_all, schema_name

st.set_page_config(
    page_title="AdventureWorks Operations Command Center",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#123B66"
BLUE = "#1769AA"
TEAL = "#159A9C"
CYAN = "#45B8C8"
GOLD = "#E7A91C"
RED = "#C94C4C"
GREEN = "#2E8B57"
MUTED = "#6B7280"
PALETTE = [NAVY, TEAL, GOLD, CYAN, BLUE, RED, GREEN]

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2.5rem;}
    [data-testid="stSidebar"] {background: linear-gradient(180deg, #0b2948 0%, #123b66 100%);}
    [data-testid="stSidebar"] * {color: #f8fbff;}
    [data-testid="stSidebar"] code {
        color: #0b2948 !important;
        background: #c8d6e3 !important;
        border: 1px solid #aebfd0;
        border-radius: 4px;
        padding: 2px 6px;
        font-weight: 600;
    }
    [data-testid="stSidebar"] div.stButton > button {
        background: #ffffff !important;
        border: 1px solid #c8d6e3 !important;
        color: #123b66 !important;
        font-weight: 700;
    }
    [data-testid="stSidebar"] div.stButton > button * {
        color: #123b66 !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background: #1769aa !important;
        border-color: #45b8c8 !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] div.stButton > button:focus {
        box-shadow: 0 0 0 3px rgba(69, 184, 200, 0.35) !important;
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dce7f1;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 4px 14px rgba(18, 59, 102, 0.06);
    }
    div[data-testid="stMetricLabel"] {color: #52657a;}
    .hero {
        padding: 20px 24px;
        border-radius: 16px;
        background: linear-gradient(115deg, #123b66 0%, #1769aa 58%, #159a9c 100%);
        color: white;
        margin-bottom: 16px;
    }
    .hero h1 {margin: 0; font-size: 2rem; color: white;}
    .hero p {margin: 6px 0 0 0; opacity: .9;}
    .insight {
        background: #f5fafc;
        border-left: 5px solid #159a9c;
        padding: 12px 15px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .warning {
        background: #fff8e5;
        border-left: 5px solid #e7a91c;
        padding: 12px 15px;
        border-radius: 8px;
        margin: 8px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def money(value: float | int | None, compact: bool = True) -> str:
    if value is None or pd.isna(value):
        return "—"
    number = float(value)
    if compact and abs(number) >= 1_000_000:
        return f"${number / 1_000_000:,.2f}M"
    if compact and abs(number) >= 1_000:
        return f"${number / 1_000:,.1f}K"
    return f"${number:,.2f}"


def whole(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.0f}"


def percent(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.1%}"


def polish(fig: go.Figure, height: int = 390) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=48, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color="#263648"),
        legend_title_text="",
        hoverlabel=dict(bgcolor="white"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e8eef4", zeroline=False)
    return fig


def show_plot(fig: go.Figure, height: int = 390) -> None:
    st.plotly_chart(
        polish(fig, height),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )


def section_header(title: str, subtitle: str) -> None:
    st.markdown(f"### {title}")
    st.caption(subtitle)


def normalize_dates(data: dict[str, pd.DataFrame]) -> None:
    date_columns = {
        "executive": ["data_through_date"],
        "monthly": ["performance_month"],
        "products": ["latest_sale_date", "latest_purchase_date", "latest_inventory_modified_date"],
        "customers": ["first_order_date", "last_order_date"],
        "employees": ["hire_date", "first_purchase_order_date", "latest_purchase_order_date"],
    }
    for dataset, columns in date_columns.items():
        for column in columns:
            if column in data[dataset].columns:
                data[dataset][column] = pd.to_datetime(data[dataset][column], errors="coerce")




st.sidebar.markdown("## AdventureWorks")
st.sidebar.caption("Operations Command Center")
page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Overview",
        "Product & Inventory",
        "Customer Intelligence",
        #"Purchasing & Buyers",
    ],
)
st.sidebar.markdown("---")
st.sidebar.caption(f"Source: `{database_name()}.{schema_name()}`")
if st.sidebar.button("Refresh cached data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

try:
    with st.spinner("Loading curated Snowflake marts..."):
        data = load_all()
    normalize_dates(data)
except Exception as exc:
    st.error("The application could not load its five curated marts.")
    st.code(str(exc))
    st.info("Verify the Snowflake connection and SELECT access to the MARTS schema.")
    st.stop()

executive = data["executive"]
monthly = data["monthly"].sort_values("performance_month")
products = data["products"]
customers = data["customers"]
employees = data["employees"]

if executive.empty:
    st.error("The executive KPI mart contains no rows. Run the dbt build before opening the app.")
    st.stop()

kpi = executive.iloc[0]
data_date = kpi.get("data_through_date")
through_label = data_date.strftime("%d %b %Y") if pd.notna(data_date) else "latest available load"

st.markdown(
    '<div class="hero"><h1>AdventureWorks Operations Command Center</h1>'
    f'<p>Cross-functional sales, customer, inventory and purchasing intelligence through {through_label}.</p></div>',
    unsafe_allow_html=True,
)

if page == "Executive Overview":
    cols = st.columns(6)
    metrics = [
        ("Net sales", money(kpi.get("net_sales_amount"))),
        ("Estimated margin", money(kpi.get("estimated_margin_amount"))),
        ("Margin rate", percent(kpi.get("estimated_margin_rate"))),
        ("Sales orders", whole(kpi.get("sales_order_count"))),
        ("Active customers", whole(kpi.get("active_customer_count"))),
        ("Inventory value", money(kpi.get("estimated_inventory_value"))),
    ]
    for column, (label, value) in zip(cols, metrics):
        column.metric(label, value)

    left, right = st.columns([1.7, 1])
    with left:
        section_header("Sales trend", "Monthly value movement across revenue ")
        trend = monthly.melt(
            id_vars="performance_month",
            value_vars=["net_sales_amount"],
            var_name="metric",
            value_name="amount",
        )
        trend["metric"] = trend["metric"].map(
            {"net_sales_amount": "Net sales"}
        )
        fig = px.line(
            trend,
            x="performance_month",
            y="amount",
            color="metric",
            markers=True,
            color_discrete_map={"Net sales": NAVY},
        )
        fig.update_yaxes(tickprefix="$", tickformat="~s")
        show_plot(fig, 410)

    with right:
        section_header("Operational health", "Current fulfillment and inventory indicators")
        on_time = float(kpi.get("purchasing_on_time_rate") or 0)
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=on_time * 100,
                number={"suffix": "%", "font": {"color": NAVY}},
                title={"text": "Purchase-line on-time rate"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": TEAL},
                    "steps": [
                        {"range": [0, 75], "color": "#f9d7d7"},
                        {"range": [75, 90], "color": "#fff0c2"},
                        {"range": [90, 100], "color": "#d8f0e3"},
                    ],
                    "threshold": {"line": {"color": GOLD, "width": 4}, "value": 90},
                },
            )
        )
        show_plot(gauge, 310)
        #st.metric("Rejected purchase units", whole(kpi.get("rejected_units")))

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        section_header("Estimated margin trend", "Margin uses product standard cost and is not an accounting measure")
        fig = px.area(
            monthly,
            x="performance_month",
            y="estimated_margin_amount",
            color_discrete_sequence=[TEAL],
        )
        fig.update_yaxes(tickprefix="$", tickformat="~s")
        show_plot(fig, 330)
    with bottom_right:
        section_header("Inventory status", "Number of products by replenishment status")
        status = products.groupby("inventory_status", dropna=False).size().reset_index(name="product_count")
        fig = px.pie(
            status,
            names="inventory_status",
            values="product_count",
            hole=0.58,
            color_discrete_sequence=PALETTE,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        show_plot(fig, 330)

elif page == "Product & Inventory":
    categories = sorted(products["product_category_name"].dropna().astype(str).unique())
    statuses = sorted(products["inventory_status"].dropna().astype(str).unique())
    c1, c2 = st.columns(2)
    selected_categories = c1.multiselect("Product category", categories, default=categories)
    selected_statuses = c2.multiselect("Inventory status", statuses, default=statuses)
    filtered = products[
        products["product_category_name"].astype(str).isin(selected_categories)
        & products["inventory_status"].astype(str).isin(selected_statuses)
    ].copy()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Products", whole(filtered["product_key"].nunique()))
    m2.metric("Net sales", money(filtered["net_sales_amount"].sum()))
    m3.metric("Estimated margin", money(filtered["estimated_margin_amount"].sum()))
    m4.metric("Inventory units", whole(filtered["inventory_units"].sum()))

    left, right = st.columns([1.2, 1])
    with left:
        section_header("Product portfolio", "Net sales contribution by category, subcategory and product")
        tree = filtered.nlargest(80, "net_sales_amount").copy()
        tree[["product_category_name", "product_subcategory_name", "product_name"]] = tree[
            ["product_category_name", "product_subcategory_name", "product_name"]
        ].fillna("Unclassified")
        fig = px.treemap(
            tree,
            path=["product_category_name", "product_subcategory_name", "product_name"],
            values="net_sales_amount",
            color="estimated_margin_rate",
            color_continuous_scale="Tealgrn",
            hover_data=["units_sold", "inventory_units"],
        )
        show_plot(fig, 470)
    with right:
        section_header("Demand versus stock", "Bubble size represents net sales")
        scatter = filtered.copy()
        scatter["bubble_sales"] = scatter["net_sales_amount"].clip(lower=0) + 1
        fig = px.scatter(
            scatter,
            x="inventory_units",
            y="units_sold",
            size="bubble_sales",
            color="inventory_status",
            hover_name="product_name",
            hover_data=["product_category_name", "net_sales_amount", "estimated_margin_rate"],
            color_discrete_sequence=PALETTE,
            size_max=42,
        )
        show_plot(fig, 470)

    low_stock = filtered[
        filtered["inventory_status"].isin(["OUT OF STOCK", "BELOW REORDER POINT", "BELOW SAFETY STOCK"])
    ].copy()
    low_stock["sales_at_risk_score"] = low_stock["net_sales_amount"] / (low_stock["inventory_units"] + 1)
    section_header("Priority replenishment list", "Low-stock products ranked by historical net sales per available unit")
    st.dataframe(
        low_stock.nlargest(20, "sales_at_risk_score")[[
            "product_number",
            "product_name",
            "product_category_name",
            "inventory_status",
            "inventory_units",
            "reorder_point",
            "units_sold",
            "net_sales_amount",
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "net_sales_amount": st.column_config.NumberColumn("Net sales", format="$%.2f"),
            "inventory_units": st.column_config.NumberColumn("Inventory units", format="%d"),
        },
    )

elif page == "Customer Intelligence":
    segments = sorted(customers["rfm_segment"].dropna().astype(str).unique())
    groups = sorted(customers["territory_group"].dropna().astype(str).unique())
    c1, c2 = st.columns(2)
    selected_segments = c1.multiselect("RFM segment", segments, default=segments)
    selected_groups = c2.multiselect("Territory group", groups, default=groups)
    filtered = customers[
        customers["rfm_segment"].astype(str).isin(selected_segments)
        & customers["territory_group"].astype(str).isin(selected_groups)
    ].copy()

    buyers = filtered[filtered["total_orders"] > 0]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Customers", whole(filtered["customer_key"].nunique()))
    m2.metric("Customers with orders", whole(buyers["customer_key"].nunique()))
    m3.metric("Order-total revenue", money(filtered["lifetime_revenue"].sum()))
    m4.metric("Average customer value", money(buyers["lifetime_revenue"].mean()))

    left, right = st.columns(2)
    with left:
        section_header("RFM portfolio", "Customer count and lifetime revenue by behavioral segment")
        segment_summary = filtered.groupby("rfm_segment", as_index=False).agg(
            customer_count=("customer_key", "nunique"),
            lifetime_revenue=("lifetime_revenue", "sum"),
        )
        fig = px.bar(
            segment_summary.sort_values("lifetime_revenue"),
            y="rfm_segment",
            x="lifetime_revenue",
            color="customer_count",
            orientation="h",
            color_continuous_scale="Teal",
            hover_data=["customer_count"],
        )
        fig.update_xaxes(tickprefix="$", tickformat="~s")
        show_plot(fig, 420)
    with right:
        section_header("Value and recency", "Identify high-value customers whose engagement is declining")
        scatter = buyers.copy()
        scatter["bubble_orders"] = scatter["total_orders"].clip(lower=1)
        fig = px.scatter(
            scatter,
            x="recency_days",
            y="lifetime_revenue",
            size="bubble_orders",
            color="rfm_segment",
            hover_name="customer_name",
            hover_data=["customer_type", "total_orders", "average_order_value", "territory_name"],
            color_discrete_sequence=PALETTE,
            size_max=36,
        )
        fig.update_yaxes(tickprefix="$", tickformat="~s")
        show_plot(fig, 420)

    at_risk = filtered[
        filtered["customer_activity_status"].isin(["LAPSED - 180 DAYS", "INACTIVE"])
        & (filtered["lifetime_revenue"] > filtered["lifetime_revenue"].median())
    ]
    section_header("Retention opportunities", "Higher-value customers with lapsed or inactive purchasing activity")
    st.dataframe(
        at_risk.nlargest(20, "lifetime_revenue")[[
            "customer_name",
            "territory_name",
            "rfm_segment",
            "customer_activity_status",
            "recency_days",
            "total_orders",
            "lifetime_revenue",
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={"lifetime_revenue": st.column_config.NumberColumn("Order-total revenue", format="$%.2f")},
    )

elif page == "Purchasing & Buyers":
    departments = sorted(employees["department_name"].dropna().astype(str).unique())
    selected_departments = st.multiselect("Department", departments, default=departments)
    filtered = employees[
        employees["department_name"].astype(str).isin(selected_departments)
        & (employees["purchase_order_count"] > 0)
    ].copy()

    ordered_units = filtered["ordered_units"].sum()
    rejection_rate = filtered["rejected_units"].sum() / ordered_units if ordered_units else np.nan
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active buyers", whole(filtered["employee_key"].nunique()))
    m2.metric("Purchase orders", whole(filtered["purchase_order_count"].sum()))
    m3.metric("Purchase amount", money(filtered["purchase_amount"].sum()))
    m4.metric("Weighted rejection rate", percent(rejection_rate))

    left, right = st.columns(2)
    with left:
        section_header("Top buyers by managed spend", "Purchasing amount attributed to the employee on each purchase order")
        ranking = filtered.nlargest(15, "purchase_amount").sort_values("purchase_amount")
        fig = px.bar(
            ranking,
            x="purchase_amount",
            y="employee_name",
            orientation="h",
            color="on_time_delivery_rate",
            color_continuous_scale="Teal",
            hover_data=["department_name", "purchase_order_count", "vendor_count"],
        )
        fig.update_xaxes(tickprefix="$", tickformat="~s")
        show_plot(fig, 470)
    with right:
        section_header("Delivery reliability and quality", "Bubble size represents purchase amount")
        scatter = filtered.copy()
        scatter["rejection_rate"] = scatter["rejected_units"] / scatter["ordered_units"].replace(0, np.nan)
        scatter["bubble_spend"] = scatter["purchase_amount"].clip(lower=0) + 1
        fig = px.scatter(
            scatter,
            x="on_time_delivery_rate",
            y="rejection_rate",
            size="bubble_spend",
            color="department_name",
            hover_name="employee_name",
            hover_data=["purchase_order_count", "purchase_amount", "average_actual_lead_time_days"],
            color_discrete_sequence=PALETTE,
            size_max=45,
        )
        fig.update_xaxes(tickformat=".0%")
        fig.update_yaxes(tickformat=".1%")
        show_plot(fig, 470)

    section_header("Monthly procurement movement", "Spend, received units, and on-time performance")
    fig = go.Figure()
    fig.add_bar(
        x=monthly["performance_month"],
        y=monthly["purchase_amount"],
        name="Purchase amount",
        marker_color=NAVY,
    )
    fig.add_trace(
        go.Scatter(
            x=monthly["performance_month"],
            y=monthly["purchasing_on_time_rate"],
            name="On-time rate",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color=GOLD, width=3),
        )
    )
    fig.update_layout(
        yaxis=dict(title="Purchase amount", tickprefix="$", tickformat="~s"),
        yaxis2=dict(title="On-time rate", overlaying="y", side="right", tickformat=".0%", range=[0, 1.05]),
    )
    show_plot(fig, 380)


    section_header(
        "Purchasing quality exceptions",
        "Buyers with an on-time rate below 90% or a rejected-unit rate above 2%",
    )
    buyer_risk = filtered.copy()
    buyer_risk["rejection_rate"] = (
        buyer_risk["rejected_units"]
        / buyer_risk["ordered_units"].replace(0, np.nan)
    )
    buyer_risk = buyer_risk[
        (buyer_risk["on_time_delivery_rate"] < 0.90)
        | (buyer_risk["rejection_rate"] > 0.02)
    ]
    st.dataframe(
        buyer_risk.sort_values(
            ["on_time_delivery_rate", "rejection_rate"],
            ascending=[True, False],
        )[[
            "employee_name",
            "department_name",
            "purchase_order_count",
            "purchase_amount",
            "on_time_delivery_rate",
            "rejection_rate",
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "purchase_amount": st.column_config.NumberColumn(
                "Purchase amount", format="$%.2f"
            ),
            "on_time_delivery_rate": st.column_config.NumberColumn(
                "On-time rate", format="percent"
            ),
            "rejection_rate": st.column_config.NumberColumn(
                "Rejection rate", format="percent"
            ),
        },
    )

with st.expander("Metric definitions and interpretation"):
    st.markdown(
        """
* **Net sales** is sales-order-line value after line discounts; tax and freight are excluded.
* **Order-total revenue** in customer analysis comes from order headers and includes tax and freight.
* **Estimated margin** uses product standard cost and is intended for operational comparison, not accounting reporting.
* **Late order-line rate** is the share of order lines belonging to orders shipped after their due date.
* **Purchase on-time rate** is calculated at purchase-order-line grain.
* **Active customer** in the executive mart means a customer whose last purchase is within 90 days of the analysis date.
* RFM scores are relative quintiles evaluated one day after the latest order date in the dataset.
        """
    )
