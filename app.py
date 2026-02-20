import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Flinn BI Challenge",
    page_icon="📊",
    layout="wide"
)

# ─────────────────────────────────────────────
# LOAD DATA
# Reading directly from the dbt seeds folder
# In production these would be dbt model outputs from BigQuery
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    events    = pd.read_csv("seeds/backend_events.csv")
    deals     = pd.read_csv("seeds/hubspot_deals.csv")
    companies = pd.read_csv("seeds/hubspot_companies.csv")
    contacts  = pd.read_csv("seeds/hubspot_contacts.csv")

    # Parse timestamps
    events["event_timestamp"] = pd.to_datetime(events["event_timestamp"])
    deals["close_date"]       = pd.to_datetime(deals["close_date"],  errors="coerce")
    deals["create_date"]      = pd.to_datetime(deals["create_date"], errors="coerce")

    # Parse stage entry dates
    stage_cols = [
        "date_entered_pre_pitch", "date_entered_pitching",
        "date_entered_product_testing", "date_entered_price_offering",
        "date_entered_contract_negotiation"
    ]
    for col in stage_cols:
        deals[col] = pd.to_datetime(deals[col], errors="coerce")

    return events, deals, companies, contacts

events, deals, companies, contacts = load_data()

# ─────────────────────────────────────────────
# DERIVED DATASETS
# ─────────────────────────────────────────────
won_deals       = deals[deals["is_closed_won"] == True]
won_company_ids = won_deals["hubspot_company_id"].unique()
customer_cos    = companies[companies["company_id"].isin(won_company_ids)]

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("Flinn BI Challenge - Dashboard")
st.caption("Data sources: backend_events · hubspot_deals · hubspot_companies · hubspot_contacts")
st.divider()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Q1 · Customers",
    "Q2 · ACV",
    "Q3 · Retention",
    "Bonus · Sales Funnel"
])


# ═══════════════════════════════════════════════
# TAB 1 - Q1: How many customers do we have today?
# ═══════════════════════════════════════════════
with tab1:
    st.header("How many customers do we have today?")
    st.write(
        "A customer is defined as any company with at least one closed-won deal in HubSpot. "
        "We use deals as the source of truth rather than the lifecycle stage in contacts, "
        "since that field can lag behind actual deal status."
    )

    st.metric("Total Customers", len(won_company_ids))
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("By Country")
        by_country = (
            customer_cos["country"]
            .value_counts()
            .reset_index()
            .rename(columns={"country": "Country", "count": "Customers"})
        )
        fig = px.bar(
            by_country, x="Customers", y="Country",
            orientation="h",
            color="Customers",
            color_continuous_scale="Blues"
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("By Industry")
        by_industry = (
            customer_cos["industry"]
            .dropna()
            .value_counts()
            .reset_index()
            .rename(columns={"industry": "Industry", "count": "Customers"})
        )
        fig2 = px.bar(
            by_industry, x="Customers", y="Industry",
            orientation="h",
            color="Customers",
            color_continuous_scale="Teal"
        )
        fig2.update_layout(showlegend=False, coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)

    # Softened - flagging the discrepancy without asserting a cause
    st.caption(
        "Note: the contacts table shows 28 companies with a 'customer' lifecycle stage, "
        "vs 26 unique companies from closed-won deals. The two sources don't fully align - "
        "worth investigating which should be treated as the source of truth."
    )


# ═══════════════════════════════════════════════
# TAB 2 - Q2: What is our ACV?
# ═══════════════════════════════════════════════
with tab2:
    st.header("What is our Average Contract Value (ACV)?")
    st.write(
        "ACV is calculated as the simple average of all closed-won deal amounts."
    )

    # ACV is the answer to the question - put it in the centre
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue",          f"€{won_deals['amount'].sum():,.0f}")
    col2.metric("Average Contract Value", f"€{won_deals['amount'].mean():,.2f}")  # centre
    col3.metric("Won Contracts",          f"{len(won_deals)}")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Deal Size Distribution")
        fig = px.histogram(
            won_deals, x="amount",
            nbins=10,
            labels={"amount": "Deal Amount (€)"},
            color_discrete_sequence=["#2563eb"]
        )
        fig.update_layout(bargap=0.1)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Revenue by Deal Type")
        by_type = (
            won_deals.groupby("deal_type")["amount"]
            .agg(total="sum", count="count", avg="mean")
            .reset_index()
        )
        fig2 = px.bar(
            by_type, x="deal_type", y="total",
            labels={"deal_type": "Deal Type", "total": "Total Revenue (€)"},
            color="deal_type",
            color_discrete_sequence=["#2563eb", "#7c3aed"]
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        # Round to clean numbers
        by_type["total"] = by_type["total"].apply(lambda x: f"€{x:,.0f}")
        by_type["avg"]   = by_type["avg"].apply(lambda x: f"€{x:,.0f}")
        st.dataframe(
            by_type.rename(columns={
                "deal_type": "Type", "total": "Total Revenue",
                "count": "# Deals", "avg": "Avg Deal"
            }),
            hide_index=True
        )


# ═══════════════════════════════════════════════
# TAB 3 - Q3: Retention
# ═══════════════════════════════════════════════
with tab3:
    st.header("What is the retention of our users?")
    st.write(
        "Users are grouped by the month they first appeared in the backend events. "
        "We then check what % of each cohort came back in M1, M2, and M3."
    )

    # Build cohort retention
    df = events.copy()
    df["month"] = df["event_timestamp"].dt.to_period("M")
    cohort_map = df.groupby("user_id")["month"].min().rename("cohort")
    df = df.join(cohort_map, on="user_id")
    df["month_number"] = (df["month"] - df["cohort"]).apply(lambda x: x.n)

    retention = (
        df[df["month_number"].isin([0, 1, 2, 3])]
        .groupby(["cohort", "month_number"])["user_id"]
        .nunique()
        .unstack(fill_value=0)
        .rename(columns={0: "M0", 1: "M1", 2: "M2", 3: "M3"})
    )
    retention["M1 %"] = (retention["M1"] / retention["M0"] * 100).round(1)
    retention["M2 %"] = (retention["M2"] / retention["M0"] * 100).round(1)
    retention["M3 %"] = (retention["M3"] / retention["M0"] * 100).round(1)
    retention = retention[:-1]  # exclude current incomplete month

    st.subheader("Cohort Retention Table")
    st.dataframe(
        retention[["M0", "M1 %", "M2 %", "M3 %"]]
        .rename(columns={"M0": "Starting Users"})
        .style
        .format({"M1 %": "{:.1f}", "M2 %": "{:.1f}", "M3 %": "{:.1f}"})
        .background_gradient(subset=["M1 %", "M2 %", "M3 %"], cmap="YlGn"),
        use_container_width=True
    )

    # Grouped bar chart - cleaner than a line chart for this data
    st.subheader("Retention by Cohort")
    retention_long = retention[["M1 %", "M2 %", "M3 %"]].reset_index()
    retention_long["cohort"] = retention_long["cohort"].astype(str)
    retention_melted = retention_long.melt(id_vars="cohort", var_name="Month", value_name="Retention %")

    fig = px.bar(
        retention_melted, x="cohort", y="Retention %",
        color="Month", barmode="group",
        color_discrete_sequence=["#2563eb", "#7c3aed", "#059669"],
        labels={"cohort": "Cohort Month"}
    )
    fig.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 110])
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════
# TAB 4 - BONUS: Sales Funnel Insight
# ═══════════════════════════════════════════════
with tab4:
    st.header("Bonus Insight: The Contract Negotiation Bottleneck")

    # Softer opening - observational rather than declarative
    st.write(
        "Looking at the pipeline data, a pattern stands out: most deals that are lost "
        "have already made it through the early stages. The drop-off happens late, "
        "concentrated at Contract Negotiation - and the win rate has been declining over time."
    )
    st.divider()

    # ── Compute lost deal stage breakdown for the stat callout ──
    stage_cols_map = {
        "Pre-pitch":            "date_entered_pre_pitch",
        "Pitching":             "date_entered_pitching",
        "Product Testing":      "date_entered_product_testing",
        "Price Offering":       "date_entered_price_offering",
        "Contract Negotiation": "date_entered_contract_negotiation",
    }

    lost_deals = deals[deals["is_closed"] == True][deals["is_closed_won"] == False].copy()

    # Find last stage reached for each lost deal
    def last_stage(row):
        for stage, col in reversed(list(stage_cols_map.items())):
            if pd.notna(row[col]):
                return stage
        return "Unknown"

    lost_deals["last_stage"] = lost_deals.apply(last_stage, axis=1)
    lost_in_neg = (lost_deals["last_stage"] == "Contract Negotiation").sum()
    pct_lost_in_neg = round(lost_in_neg / len(lost_deals) * 100)

    # Stat callout - makes the 81% visible in the dashboard
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Lost Deals",               len(lost_deals))
    col_b.metric("Lost at Contract Negotiation",   lost_in_neg)
    col_c.metric("% of Losses at Last Stage",      f"{pct_lost_in_neg}%")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Pipeline Funnel")
        funnel_data = pd.DataFrame([
            {"Stage": stage, "Deals": deals[col].notna().sum()}
            for stage, col in stage_cols_map.items()
        ])
        fig = go.Figure(go.Funnel(
            y=funnel_data["Stage"],
            x=funnel_data["Deals"],
            textinfo="value+percent initial",
            marker={"color": ["#1d4ed8", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]}
        ))
        fig.update_layout(margin={"t": 20})
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Each bar shows the number of deals that entered that stage. % is relative to Pre-pitch.")
        st.caption(
            "Note: Pitching (75) shows more deals than Pre-pitch (69) because some deals "
            "skipped the Pre-pitch stage in HubSpot - stages aren't always entered sequentially. "
        )

    with col2:
        st.subheader("Contract Negotiation Outcomes")
        neg_deals = deals[deals["date_entered_contract_negotiation"].notna()].copy()
        neg_deals["outcome"] = neg_deals.apply(
            lambda r: "Won" if r["is_closed_won"] == True
                      else ("Lost" if r["is_closed"] == True else "Open"),
            axis=1
        )
        outcome_counts = neg_deals["outcome"].value_counts().reset_index()
        outcome_counts.columns = ["Outcome", "Count"]
        fig2 = px.pie(
            outcome_counts, names="Outcome", values="Count",
            color="Outcome",
            color_discrete_map={"Won": "#059669", "Lost": "#dc2626", "Open": "#d97706"},
            hole=0.4
        )
        st.plotly_chart(fig2, use_container_width=True)

        won_neg  = neg_deals[neg_deals["outcome"] == "Won"]
        lost_neg = neg_deals[neg_deals["outcome"] == "Lost"]
        st.metric("Win rate in negotiation", f"{len(won_neg)/len(neg_deals)*100:.0f}%")
        st.metric("Avg deal size - Won",     f"€{won_neg['amount'].mean():,.0f}")
        st.metric("Avg deal size - Lost",    f"€{lost_neg['amount'].mean():,.0f}")
        st.caption("Deal size is similar between won and lost")

    st.divider()

    # Win rate trend
    st.subheader("Win Rate Trend Over Time")
    st.write("Win rate has dropped significantly as deal volume has grown.")

    closed = deals[deals["is_closed"] == True].copy()
    closed = closed[closed["close_date"].notna()]
    closed["close_month"] = closed["close_date"].dt.to_period("M").astype(str)
    closed["outcome"]     = closed["is_closed_won"].apply(lambda x: "Won" if x == True else "Lost")

    monthly = (
        closed.groupby("close_month")["outcome"]
        .value_counts()
        .unstack(fill_value=0)
        .assign(total=lambda df: df.sum(axis=1))
    )
    if "Won" not in monthly.columns:
        monthly["Won"] = 0
    monthly["win_rate"] = (monthly["Won"] / monthly["total"] * 100).round(1)
    monthly = monthly.reset_index()

    fig3 = go.Figure()
    fig3.add_bar(
        x=monthly["close_month"], y=monthly.get("Won", 0),
        name="Won", marker_color="#059669"
    )
    fig3.add_bar(
        x=monthly["close_month"], y=monthly.get("Lost", 0),
        name="Lost", marker_color="#dc2626"
    )
    fig3.add_scatter(
        x=monthly["close_month"], y=monthly["win_rate"],
        name="Win Rate %", yaxis="y2",
        line={"color": "#f59e0b", "width": 3},
        mode="lines+markers"
    )
    fig3.update_layout(
        barmode="stack",
        yaxis={"title": "# Deals"},
        yaxis2={"title": "Win Rate %", "overlaying": "y", "side": "right", "range": [0, 110]},
        xaxis_tickangle=-45,
        legend={"orientation": "h", "y": -0.3}
    )
    st.plotly_chart(fig3, use_container_width=True)