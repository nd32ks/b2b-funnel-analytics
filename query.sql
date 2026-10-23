##--Query 1
SELECT a.segment,
       COUNT(*) AS leads,
       COUNT(d.deal_id) AS deals,
       COUNT(CASE WHEN d.status = 'won' THEN 1 END) AS won
FROM leads l
JOIN accounts a ON a.account_id = l.account_id
LEFT JOIN deals d ON d.account_id = l.account_id
GROUP BY a.segment
ORDER BY leads DESC

##--Query 2
SELECT a.segment,
       COUNT(*) AS leads,
       COUNT(d.deal_id) AS deals,
       COUNT(CASE WHEN d.status = 'won' THEN 1 END) AS won,
       ROUND(100.0 * deals / leads, 1) AS pct_leads_to_deal,
       ROUND(100.0 * COUNT(CASE WHEN d.status = 'won' THEN 1 END) / deals, 1) AS pct_deals_won,
FROM leads l
JOIN accounts a ON a.account_id = l.account_id
LEFT JOIN deals d ON d.account_id = l.account_id
GROUP BY a.segment
ORDER BY leads DESC

##--Query 3
SELECT a.segment,
         COUNT(*) AS won_customers,
         COUNT(d.churn_date) AS churned,
         ROUND(100.0 * COUNT(d.churn_date) / COUNT(*), 1) AS pct_churned
FROM deals d
JOIN accounts a ON a.account_id = d.account_id
WHERE d.status = 'won'
GROUP BY a.segment
ORDER BY pct_churned DESC

##--Query 4
SELECT date_trunc('month', u.usage_date) AS month,
       a.segment,
       COUNT(DISTINCT u.account_id) AS active_customers
FROM daily_usage u
JOIN accounts a ON u.account_id = a.account_id
GROUP BY month, a.segment
ORDER BY month, a.segment