Tables

1. Accounts - one row is one company
    account_id = unique account id
    company = company name
    segment = the size of the company, startup, enterprise allat
    industry = sector its involved in
    country = countrya company operates in

2. leads - one row is one lead (one company showing interest)
    lead_id = unique lead id
    account_id = which company it belongs to
    lead_date = date when they first showed interest
    source = howd they find us, inbound, outbound partner or event

3. deals — one row is one sales deal for one company
    deal_id = unique ID for this deal
    account_id = which company the deal belongs to (links to accounts)
    close_date = the date the deal was won or lost
    amount = the contract value
    status = won or lost
    churn_date = the date a won customer cancelled, empty if still active

4. daily_usage - one row is one customer's usage on one day
    account_id = which company this usage belongs to
    usage_date = day its being used
    requests = number of requests the customer made that day

Story Rules:
    1. Which segment is most common? Startups, probably.
    2. Which segment churns fastest, and which stays longest?
    3. How long does a deal take to close for each segment?
    4. How big is a typical contract for each segment?
    5. Does usage grow over time for customers who stay?

Numbers for rules:
 Share of companies
    Startup: 60%
    Mid-market: 30%
    Enterprise: 10%

Win rate on deals
    Startup: 45%
    Mid-market: 50%
    Enterprise: 35%

Days to close
    Startup: about 14
    Mid-market: about 35
    Enterprise: about 75

Typical contract
    Startup: $5,000
    Mid-market: $40,000
    Enterprise: $250,000

Churn per month
    Startup: 8%
    Mid-market: 4%
    Enterprise: 1.5%

Other
    Share of leads that reach the deal stage: 60%
    Usage grows slightly each day for customers who stay