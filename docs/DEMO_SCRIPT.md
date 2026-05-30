# 3-Minute Demo Script

## 0:00 - 0:20 Problem

"Teams promise features to customers, but the truth is scattered across sales notes, engineering tickets, GitHub PRs, Slack blockers, support tickets, revenue, and feature flags."

## 0:20 - 0:50 Coral angle

"Commitment Drift Radar uses Coral as one SQL interface across those systems. Instead of making the agent call every API separately, Coral joins the data and returns evidence."

Show:

```bash
coral sql -f coral/queries/commitment_risk.sql
```

## 0:50 - 1:40 Dashboard

Open the dashboard.

Click Acme Corp.

Say:

"Acme is critical because the promised date passed, engineering is still in progress, no merged PR exists, support tickets are open, Slack says blocked, and revenue impact is high."

## 1:40 - 2:20 Why it matters

"This catches drift before escalation, churn, or trust damage. It is not another generic incident summarizer. It prevents business/engineering misalignment."

## 2:20 - 3:00 Coral proof

Show the SQL query and the source list.

"Coral is the core engine. The agent explains Coral's joined evidence; it does not fetch provider data itself."
