# Commitment Drift Radar

Commitment Drift Radar is a Coral-powered enterprise agent for spotting customer promises that are drifting away from engineering reality.

It answers one operational question:

> Which committed customer outcomes are now risky because tickets, pull requests, blockers, support pressure, revenue, and rollout state disagree?

## Why This Matters

Customer commitments often live in a spreadsheet or CRM note. The real delivery state is scattered across Linear/Jira, GitHub, Slack, Intercom, Stripe, and LaunchDarkly. By the time a founder, PM, or support lead notices the drift, the customer is already frustrated.

This project turns that scattered evidence into a ranked risk board with an evidence pack for each promise.

## How Coral Is Used

Coral is the core data and retrieval layer.

In live mode, the backend runs this exact command:

```bash
coral sql -f coral/queries/commitment_risk.sql --format json
```

That SQL query joins Coral tables from multiple tools:

| Source | Coral table | Why it matters |
| --- | --- | --- |
| Customer promises CSV/file source | `commitments.customer_promises` | The customer, feature, due date, and join keys |
| Linear/Jira | `linear.issues` | Engineering status for the promised work |
| GitHub | `github.pulls` | Whether implementation evidence exists |
| Slack | `slack.messages` | Blocker and delay signals |
| Intercom | `intercom.conversations` | Open customer pressure |
| Stripe | `stripe.invoices` | Revenue impact |
| LaunchDarkly | `launchdarkly.feature_flags` | Whether the feature is actually enabled |

The Python backend does not manually call those provider APIs. It either:

- runs Coral SQL in live mode, or
- uses local demo CSVs to simulate the same joined result when private credentials are not available.

## Current Capabilities

- `python run.py` starts a local web app and API.
- Demo mode loads sample CSVs from `data/demo/`.
- `/api/risks` returns ranked commitment-risk rows.
- `/api/evidence/<feature_key>` returns the explanation and joined evidence for one row.
- Live Coral mode calls `coral sql -f coral/queries/commitment_risk.sql --format json`.
- The dashboard shows the Coral command, source list, risk board, metrics, and evidence panel.

## Demo Mode

Demo mode is for local review without private Linear, GitHub, Slack, Intercom, Stripe, or LaunchDarkly credentials.

```bash
cd commitment_drift_radar_v2
python run.py
```

Open:

```text
http://127.0.0.1:8080
```

Demo mode is the default. It uses:

```text
data/demo/commitments.csv
data/demo/linear_issues.csv
data/demo/github_pulls.csv
data/demo/slack_messages.csv
data/demo/intercom_conversations.csv
data/demo/stripe_invoices.csv
data/demo/launchdarkly_flags.csv
```

Important: demo mode simulates the joined Coral output so the product can be reviewed without private credentials. It is not presented as live Coral retrieval.

## Live Coral Mode

Install and configure Coral, then add the sources required by the query.

```bash
coral source discover
coral source add --interactive github
coral source add --interactive linear
coral source add --interactive slack
coral source add --interactive stripe
coral source add --interactive intercom
coral source add --interactive launchdarkly
```

Configure the customer commitments CSV/file source so it is available as:

```text
commitments.customer_promises
```

Run live mode:

```bash
COMMITMENT_RADAR_MODE=coral python run.py
```

PowerShell:

```powershell
$env:COMMITMENT_RADAR_MODE = "coral"
python run.py
```

Manual Coral proof command:

```bash
coral sql -f coral/queries/commitment_risk.sql --format json
```

If Coral is not installed or a source is missing, the app returns a clear backend error instead of silently falling back and pretending.

## Core SQL Query

The main query lives here:

```text
coral/queries/commitment_risk.sql
```

It is structured as:

1. Aggregate support pressure from Intercom.
2. Aggregate paid revenue from Stripe.
3. Find blocker language in Slack.
4. Match GitHub PRs to the Linear/Jira key or feature key.
5. Read LaunchDarkly rollout state.
6. Join everything to the customer promise ledger.
7. Emit a risk level: `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`.

## Deploy

### Render With Docker

This repo includes:

```text
Dockerfile
render.yaml
requirements.txt
```

For a credential-free deployment, use demo mode:

```bash
docker build -t commitment-drift-radar .
docker run -p 8080:8080 -e COMMITMENT_RADAR_HOST=0.0.0.0 commitment-drift-radar
```

Render can deploy directly from `render.yaml`. The default deployment runs in demo mode because hosted live Coral mode needs provider credentials and a Coral CLI installation in the runtime image.

For live Coral deployment, install Coral in the image or runtime, configure source credentials as secrets, and set:

```text
COMMITMENT_RADAR_MODE=coral
COMMITMENT_RADAR_HOST=0.0.0.0
```

## Project Structure

```text
backend/                  Python HTTP server, Coral adapter, demo engine, scoring, explainer
coral/queries/             Coral SQL queries
coral/source_specs/        Example customer-promises source shape
data/demo/                 Credential-free demo CSVs
static/                    Dashboard UI
Dockerfile                 Container deployment
render.yaml                Render deployment blueprint
```

## Enterprise Agent Use Case

Commitment Drift Radar is an enterprise workflow agent for customer-success, product, engineering, and founder teams. Coral gives it cross-source SQL retrieval; the app turns the joined result into ranked risk, evidence, and recommended action.
