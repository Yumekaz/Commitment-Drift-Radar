# Commitment Drift Radar

**Commitment Drift Radar** is a Coral-powered enterprise agent that finds customer promises drifting away from engineering reality.

It joins customer commitments, engineering tickets, pull requests, Slack blockers, support tickets, revenue, and rollout status into one risk report.

This version is intentionally **hackathon-demo ready**:

- Runs immediately in **demo mode** without credentials.
- Has a simple web dashboard.
- Includes real Coral SQL queries under `coral/queries/`.
- Includes a Python Coral adapter that can call `coral sql` in live mode.
- Includes setup scripts and docs for using the official `withcoral/coral` repo/CLI.

## Why this uses Coral properly

Coral is the retrieval/correlation layer.

The project is designed around this split:

```text
Coral = cross-source SQL joins + source auth + local querying
Backend = runs Coral query + scores risk + serves API
Frontend = visual dashboard
LLM/agent = explains the joined evidence
```

The important part is that the backend does **not** manually call GitHub, Slack, Linear, Stripe, or Intercom APIs one by one. In live mode, it calls Coral SQL.

## Quick demo

```bash
cd commitment_drift_radar_v2
python run.py
```

Open:

```text
http://127.0.0.1:8080
```

Demo mode uses CSV data in `data/demo/`.

## Live Coral mode

1. Install Coral.

```bash
brew install withcoral/tap/coral
```

2. Add sources.

```bash
coral source discover
coral source add --interactive github
coral source add --interactive linear
coral source add --interactive slack
coral source add --interactive stripe
coral source add --interactive intercom
coral source add --interactive launchdarkly
```

3. Run the app in live Coral mode.

```bash
COMMITMENT_RADAR_MODE=coral python run.py
```

The app will run:

```bash
coral sql -f coral/queries/commitment_risk.sql --format json
```

If Coral is missing or the query fails, the app returns a clear error instead of pretending.

## Use the Coral repo

For hackathon work, you normally **do not copy Coral source code into your app**. You install or clone Coral separately and use its CLI/MCP interface.

To clone the official Coral repo locally:

```bash
./scripts/clone_coral_repo.sh
```

That clones:

```text
https://github.com/withcoral/coral
```

into:

```text
vendor/coral
```

The cloned repo is intentionally not included in this zip because it should be fetched fresh from GitHub.

## Project structure

```text
commitment_drift_radar_v2/
├── run.py
├── backend/
│   ├── app_server.py
│   ├── coral_client.py
│   ├── demo_engine.py
│   ├── explainer.py
│   └── risk.py
├── static/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── data/demo/
│   ├── commitments.csv
│   ├── github_pulls.csv
│   ├── linear_issues.csv
│   ├── slack_messages.csv
│   ├── stripe_invoices.csv
│   ├── intercom_conversations.csv
│   └── launchdarkly_flags.csv
├── coral/
│   ├── queries/
│   │   ├── commitment_risk.sql
│   │   ├── evidence_pack.sql
│   │   └── blocker_scan.sql
│   └── source_specs/
│       └── customer_promises.example.yml
├── scripts/
│   ├── clone_coral_repo.sh
│   ├── setup_coral_sources.sh
│   └── run_demo.sh
└── docs/
    ├── CORAL_USAGE.md
    ├── DEMO_SCRIPT.md
    └── PITCH.md
```

## Submission checklist

- GitHub repo link
- Deployed link or demo URL
- YouTube demo under 3 minutes
- README section explaining Coral usage
- Screenshot showing Coral query or setup
- Star Coral repo and join Coral Discord as required by the hackathon
