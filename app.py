import altair as alt
import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="B2B Funnel Analytics", layout="wide")

SEGMENTS = ["startup", "midmarket", "enterprise"]
TABLES = ["accounts", "leads", "deals", "daily_usage"]

# one colour per segment / per funnel stage, reused in every chart
SEGMENT_COLORS = ["#3b82f6", "#f59e0b", "#10b981"]
STAGE_COLORS = ["#94a3b8", "#3b82f6", "#10b981"]
RATE_COLORS = ["#3b82f6", "#10b981"]
CHURN_COLOR = ["#ef4444"]

CHART_H = 385

# Tighten the page so everything fits in one 16:9 screen (1920x1080 or similar).
st.markdown(
    """
    <style>
      header[data-testid="stHeader"], footer, #MainMenu {display: none;}
      .block-container {padding: 1.1rem 2.2rem 0.6rem 2.2rem; max-width: 100%;}
      h1 {font-size: 1.9rem !important; padding: 0 0 0.1rem 0 !important;}
      .ct {font-size: 1.05rem; font-weight: 600; margin: 0.1rem 0 0.1rem 0.2rem;}
      [data-testid="stMetric"] {background: rgba(148,163,184,0.12);
          padding: 0.5rem 0.9rem; border-radius: 10px;}
      [data-testid="stMetricLabel"] p {font-size: 0.8rem;}
      [data-testid="stMetricValue"] {font-size: 1.7rem;}
      [data-testid="stVerticalBlockBorderWrapper"] {padding: 0.15rem 0.3rem;}
      div[data-testid="stCaptionContainer"] p {font-size: 0.82rem; margin: 0;}
      div[data-testid="stVerticalBlock"] {gap: 0.55rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def run(sql: str):
    """Run a SQL query over the CSVs in data/ and return a DataFrame.

    Uses an in-memory DuckDB, so no file lock clashes with the notebook.
    """
    con = duckdb.connect()
    for table in TABLES:
        con.execute(
            f"CREATE VIEW {table} AS SELECT * FROM read_csv_auto('data/{table}.csv')"
        )
    df = con.sql(sql).df()
    con.close()
    return df


# ------------------------------------------------------------------ queries
FUNNEL_SQL = """
SELECT a.segment,
       COUNT(*) AS leads,
       COUNT(d.deal_id) AS deals,
       COUNT(CASE WHEN d.status = 'won' THEN 1 END) AS won
FROM leads l
JOIN accounts a ON a.account_id = l.account_id
LEFT JOIN deals d ON d.account_id = l.account_id
GROUP BY a.segment
"""

RATES_SQL = """
SELECT a.segment,
       COUNT(*) AS leads,
       COUNT(d.deal_id) AS deals,
       COUNT(CASE WHEN d.status = 'won' THEN 1 END) AS won,
       ROUND(100.0 * COUNT(d.deal_id) / COUNT(*), 1) AS pct_leads_to_deal,
       ROUND(100.0 * COUNT(CASE WHEN d.status = 'won' THEN 1 END) / COUNT(d.deal_id), 1) AS pct_deals_won
FROM leads l
JOIN accounts a ON a.account_id = l.account_id
LEFT JOIN deals d ON d.account_id = l.account_id
GROUP BY a.segment
"""

CHURN_SQL = """
SELECT a.segment,
       COUNT(*) AS won_customers,
       COUNT(d.churn_date) AS churned,
       ROUND(100.0 * COUNT(d.churn_date) / COUNT(*), 1) AS pct_churned
FROM deals d
JOIN accounts a ON a.account_id = d.account_id
WHERE d.status = 'won'
GROUP BY a.segment
"""

ACTIVE_SQL = """
SELECT date_trunc('month', u.usage_date) AS month,
       a.segment,
       COUNT(DISTINCT u.account_id) AS active_customers
FROM daily_usage u
JOIN accounts a ON u.account_id = a.account_id
GROUP BY date_trunc('month', u.usage_date), a.segment
ORDER BY month, a.segment
"""


def by_segment(df):
    """Index by segment in a fixed order so charts always look the same."""
    return df.set_index("segment").reindex(SEGMENTS)


funnel = by_segment(run(FUNNEL_SQL))
rates = by_segment(run(RATES_SQL))
churn = by_segment(run(CHURN_SQL))
active = run(ACTIVE_SQL)
wide = active.pivot(index="month", columns="segment", values="active_customers")[SEGMENTS]
wide = wide.fillna(0)

# ------------------------------------------------------------------ header
head, m1, m2, m3, m4 = st.columns([2.6, 1, 1, 1, 1], vertical_alignment="center")
with head:
    st.title("B2B Funnel Analytics")
    st.caption(
        "Synthetic SaaS dataset: 600 companies, their leads, deals, churn and daily "
        "usage, generated in Python and queried with SQL in DuckDB."
    )
m1.metric("Leads", f"{funnel['leads'].sum():,}")
m2.metric("Deals", f"{funnel['deals'].sum():,}")
m3.metric("Won customers", f"{funnel['won'].sum():,}")
m4.metric("Churned customers", f"{churn['churned'].sum():,}")

# ------------------------------------------------------------------ chart helpers
def bar_chart(df, cols, colors, labels=None):
    """Grouped bars per segment, in SEGMENTS order, with value labels."""
    long = (
        df[cols].reset_index().melt("segment", var_name="series", value_name="value")
    )
    if labels:
        long["series"] = long["series"].map(labels)
    names = list(dict.fromkeys(long["series"]))
    base = alt.Chart(long).encode(
        x=alt.X("segment:N", sort=SEGMENTS, title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("series:N", sort=names),
        y=alt.Y("value:Q", title=None,
                scale=alt.Scale(domainMax=float(long["value"].max()) * 1.15)),
        color=alt.Color(
            "series:N",
            scale=alt.Scale(domain=names, range=colors),
            legend=alt.Legend(title=None, orient="top") if len(names) > 1 else None,
        ),
    )
    bars = base.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    text = base.mark_text(dy=-6, fontSize=12).encode(
        text=alt.Text("value:Q", format="~g"), color=alt.value("#64748b")
    )
    return (bars + text).properties(height=CHART_H)


def line_chart(wide_df):
    long = wide_df.reset_index().melt("month", var_name="segment", value_name="customers")
    return (
        alt.Chart(long)
        .mark_line(strokeWidth=2.5)
        .encode(
            x=alt.X("month:T", title=None, axis=alt.Axis(format="%b %y", labelAngle=0)),
            y=alt.Y("customers:Q", title=None),
            color=alt.Color(
                "segment:N",
                sort=SEGMENTS,
                scale=alt.Scale(domain=SEGMENTS, range=SEGMENT_COLORS),
                legend=alt.Legend(title=None, orient="top"),
            ),
        )
        .properties(height=CHART_H)
    )


# ------------------------------------------------------------------ 2 x 2 grid
left, right = st.columns(2)
left2, right2 = st.columns(2)

with left.container(border=True):
    st.markdown('<div class="ct">1. Funnel by segment</div>', unsafe_allow_html=True)
    st.altair_chart(
        bar_chart(funnel, ["leads", "deals", "won"], STAGE_COLORS),
        use_container_width=True,
    )
    st.caption(
        f"**Insight:** startups bring the most leads ({funnel.loc['startup', 'leads']}) "
        f"and the most wins ({funnel.loc['startup', 'won']}); enterprise is small "
        f"({funnel.loc['enterprise', 'won']} won) but far bigger per contract."
    )

with right.container(border=True):
    st.markdown('<div class="ct">2. Conversion rates (%)</div>', unsafe_allow_html=True)
    st.altair_chart(
        bar_chart(
            rates,
            ["pct_leads_to_deal", "pct_deals_won"],
            RATE_COLORS,
            labels={"pct_leads_to_deal": "leads to deal", "pct_deals_won": "deals won"},
        ),
        use_container_width=True,
    )
    st.caption(
        f"**Insight:** enterprise leads reach a deal most often "
        f"({rates.loc['enterprise', 'pct_leads_to_deal']}%) but are won least "
        f"({rates.loc['enterprise', 'pct_deals_won']}% vs "
        f"{rates.loc['startup', 'pct_deals_won']}% for startups)."
    )

with left2.container(border=True):
    st.markdown(
        '<div class="ct">3. Churn by segment (% of won customers)</div>',
        unsafe_allow_html=True,
    )
    st.altair_chart(
        bar_chart(churn, ["pct_churned"], CHURN_COLOR), use_container_width=True
    )
    st.caption(
        f"**Insight:** {churn.loc['startup', 'pct_churned']}% of won startups have "
        f"cancelled vs {churn.loc['midmarket', 'pct_churned']}% of mid-market and "
        f"{churn.loc['enterprise', 'pct_churned']}% of enterprise. Retention effort "
        f"is best spent on startups."
    )

with right2.container(border=True):
    st.markdown('<div class="ct">4. Active customers per month</div>', unsafe_allow_html=True)
    st.altair_chart(line_chart(wide), use_container_width=True)
    peak_month = wide["startup"].idxmax().strftime("%B %Y")
    st.caption(
        f"**Insight:** active startups peak in {peak_month} at "
        f"{int(wide['startup'].max())}, then fall to {int(wide['startup'].iloc[-1])} "
        f"as churn outpaces new deals; mid-market and enterprise hold steady."
    )
