# B2B funnel analytics

I made up a software company that sells to other businesses, generated its data, and then used SQL to answer a few questions about its customers. A small Streamlit dashboard shows the answers.

The data is fake. I wrote the rules that create it (startups cancel fast, enterprise deals are big and slow), so none of this is a discovery about the real world. What I was really testing is whether my queries would find the patterns I'd planted. They did.

## The questions

- Where do leads drop off on the way to becoming customers?
- Which kinds of customers cancel fastest?
- How many customers are actually using the product each month?

## What's in here

- `generate_data.py` builds four tables (accounts, leads, deals, daily_usage) with pandas and Faker, then saves them to `funnel.duckdb`.
- `explore.ipynb` has the SQL I wrote for each question.
- `app.py` is the dashboard.

## What I found

600 leads turned into 380 deals and 166 won customers. Split by company size:

| Segment | Leads | Reach a deal | Deals won | Churned |
|---|---|---|---|---|
| Startup | 361 | 62.9% | 44.9% | 58.8% |
| Mid-market | 184 | 59.2% | 47.7% | 36.5% |
| Enterprise | 55 | 80.0% | 27.3% | 25.0% |

Enterprise leads are the most likely to reach a deal and the least likely to close one. If I worked at this company I'd want to know what goes wrong in those negotiations.

Startups are the opposite problem. They're easy to win and they leave. Almost 59% of the ones we won have cancelled. Active startup customers peaked at 55 in December 2025 and were down to 44 by March 2026, while mid-market held steady around 33 and enterprise crept up to 11. Keeping startups would do more for this company than finding more of them.

## What I'd be careful about

Only 12 enterprise deals were won, so those numbers could move a lot with a different random seed. The churn percentages also count everyone who ever signed up, which means older customers had more time to cancel than recent ones. A retention curve by signup month would fix that. It's the first thing I'd add, and it needs window functions, which I haven't used yet.

I also didn't run any significance tests. The gaps between segments are big, but I haven't checked that they're real.

## Running it

```
pip install duckdb pandas numpy faker streamlit
python generate_data.py
streamlit run app.py
```

Streamlit prints a local link. Open it in your browser.
