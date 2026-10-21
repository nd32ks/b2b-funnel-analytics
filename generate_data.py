import os
import duckdb
import pandas as pd
import numpy as np
import faker as fk
from datetime import date, timedelta

rng = np.random.default_rng(42)
fk.Faker.seed(42)
faker = fk.Faker()

# ------ Settings
comp_number = 600
enddate = date(2026, 3, 31)
END = pd.Timestamp(enddate)

company_shares = {"startup": 0.6, "midmarket": 0.3, "enterprise": 0.1}
winrate = {"startup": 0.45, "midmarket": 0.50, "enterprise": 0.35}
daystoclose = {"startup": 14, "midmarket": 35, "enterprise": 75}
typicalcontract = {"startup": 5000, "midmarket": 40000, "enterprise": 250000}
churnpermo = {"startup": 0.08, "midmarket": 0.04, "enterprise": 0.015}
dailyrequests = {"startup": 200, "midmarket": 2000, "enterprise": 15000}

industries = ["SaaS", "Fintech", "Healthcare", "Retail", "Manufacturing", "Logistics"]
countries = ["USA", "UK", "Germany", "Singapore", "Australia", "Canada"]
sources = ["inbound", "outbound", "partner", "event"]

# ------ Accounts
accounts = pd.DataFrame({
    "account_id": range(1, comp_number + 1),
    "company": [faker.company() for _ in range(comp_number)],
    "segment": rng.choice(list(company_shares.keys()), size=comp_number,
                          p=list(company_shares.values())),
    "industry": rng.choice(industries, size=comp_number),
    "country": rng.choice(countries, size=comp_number),
})

# ------ Leads
lead_start = enddate - timedelta(days=730)
lead_end = enddate - timedelta(days=120)   # leave time for deals to close

leads = pd.DataFrame({
    "lead_id": range(1, comp_number + 1),
    "account_id": accounts["account_id"],
    "lead_date": pd.to_datetime(
        [faker.date_between(start_date=lead_start, end_date=lead_end)
         for _ in range(comp_number)]),
    "source": rng.choice(sources, size=comp_number, p=[0.4, 0.3, 0.2, 0.1]),
})

# ------ Deals
df = pd.DataFrame({
    "account_id": accounts["account_id"],
    "segment": accounts["segment"],
    "lead_date": leads["lead_date"],
})
N = len(df)
seg = df["segment"]

df["has_deal"] = rng.random(N) < 0.60
df["won"] = df["has_deal"] & (rng.random(N) < seg.map(winrate))

days_to_close = rng.poisson(seg.map(daystoclose))
df["close_date"] = df["lead_date"] + pd.to_timedelta(days_to_close, unit="D")

df["amount"] = (seg.map(typicalcontract) * rng.lognormal(0, 0.4, N)).round(-2)

days_to_churn = rng.geometric(seg.map(churnpermo) / 30)
churn = df["close_date"] + pd.to_timedelta(days_to_churn, unit="D")
df["churn_date"] = churn.where(df["won"] & (churn <= END))

deals = df[df["has_deal"]].reset_index(drop=True)
deals.insert(0, "deal_id", range(1, len(deals) + 1))
deals["status"] = np.where(deals["won"], "won", "lost")
deals = deals[["deal_id", "account_id", "close_date", "amount", "status", "churn_date"]]

# ------ Daily usage
won = deals[deals["status"] == "won"].merge(accounts[["account_id", "segment"]],
                                            on="account_id")
pieces = []
for r in won.itertuples():
    start = r.close_date
    last = END if pd.isna(r.churn_date) else r.churn_date
    n_days = (last - start).days
    if n_days <= 0:
        continue
    growth = 1 + 0.004 * np.arange(n_days)
    pieces.append(pd.DataFrame({
        "account_id": r.account_id,
        "usage_date": pd.date_range(start, periods=n_days, freq="D"),
        "requests": rng.poisson(dailyrequests[r.segment] * growth),
    }))
daily_usage = pd.concat(pieces, ignore_index=True)

# ------ Save to CSV and DuckDB
os.makedirs("data", exist_ok=True)
con = duckdb.connect("funnel.duckdb")
for name, table in [("accounts", accounts), ("leads", leads),
                    ("deals", deals), ("daily_usage", daily_usage)]:
    table.to_csv(f"data/{name}.csv", index=False)
    con.register("tmp", table)
    con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM tmp")
    con.unregister("tmp")
    print(f"{name:12s} {len(table):>7,} rows")
con.close()

# ------ Checks
print(len(deals), "deals;", (deals["status"] == "won").sum(), "won")
print("last usage date:", daily_usage["usage_date"].max())
u = daily_usage.merge(accounts[["account_id", "segment"]], on="account_id")
print(u.groupby("segment")["requests"].mean().round())
print("lost with churn_date:", deals.loc[deals["status"] == "lost", "churn_date"].notna().sum())