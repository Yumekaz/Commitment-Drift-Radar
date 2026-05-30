# Commitment Drift Radar

Commitment Drift Radar is a Coral-powered risk dashboard for teams that make customer commitments before the engineering work is fully shipped.

It finds promises that are drifting away from reality by joining customer commitments with engineering tickets, pull requests, support pressure, blocker messages, revenue, and rollout state.

## The Problem

In B2B product teams, a customer promise might live in a spreadsheet, while the actual delivery state is spread across Linear or Jira, GitHub, Slack, Intercom, Stripe, and LaunchDarkly.

That split creates a dangerous blind spot:

```text
Sales or success promised something.
Engineering reality changed.
Support pressure increased.
Revenue risk grew.
Nobody saw the full picture early enough.
```

Commitment Drift Radar turns that scattered evidence into one ranked view.

## What The App Shows

The dashboard highlights:

- which customer commitments are at risk
- why each commitment is risky
- which systems contributed evidence
- whether the public app is using sample data or live Coral output
- the exact Coral SQL query used for the live data path

Each risk row can be opened into an evidence pack showing the promise date, engineering status, pull request state, Slack blocker signal, support pressure, revenue impact, and rollout flag state.

## How Coral Is Used

Coral is the intended live data and retrieval layer for this project.

In live mode, the backend does not manually call GitHub, Slack, Stripe, Intercom, Linear, or LaunchDarkly APIs. It calls the official Coral CLI:

```bash
coral sql -f coral/queries/commitment_risk.sql --format json
```

The SQL query joins these Coral tables:

| Data source | Coral table used by the query | Purpose |
| --- | --- | --- |
| Customer promise ledger | `commitments.customer_promises` | Customer, feature, due date, and join keys |
| Linear/Jira | `linear.issues` | Engineering delivery state |
| GitHub | `github.pulls` | Implementation and merge evidence |
| Slack | `slack.messages` | Blocker and delay signals |
| Intercom | `intercom.conversations` | Customer support pressure |
| Stripe | `stripe.invoices` | Revenue impact |
| LaunchDarkly | `launchdarkly.feature_flags` | Whether the feature reached the customer |

The core query is in:

```text
coral/queries/commitment_risk.sql
```

The Python wrapper that runs Coral live mode is:

```text
backend/coral_client.py
```

## Public Demo Versus Live Coral Mode

The public deployment is intentionally safe to open without private company credentials.

By default, it runs in demo mode:

```text
COMMITMENT_RADAR_MODE=demo
```

Demo mode uses sample CSV files from:

```text
data/demo/
```

That means the deployed demo is not claiming to pull live GitHub, Slack, Stripe, Intercom, Linear, or LaunchDarkly data. It uses a sample dataset to demonstrate the workflow.

Live Coral mode is different:

```text
COMMITMENT_RADAR_MODE=coral
```

In live mode, the backend executes:

```bash
coral sql -f coral/queries/commitment_risk.sql --format json
```

If the Coral CLI is missing, or if the required Coral sources are not configured, the app returns an explicit error instead of silently falling back to sample data.

## Try The Demo Locally

```bash
python run.py
```

Open:

```text
http://127.0.0.1:8080
```

The dashboard will show:

- `DEMO MODE / SAMPLE DATA`
- current data mode
- source table list
- the Coral SQL command
- a `Show SQL joins` button that reveals the query used by live mode

## Run With Live Coral

Install and configure Coral from the official `withcoral/coral` project, then configure the sources required by `coral/queries/commitment_risk.sql`.

At minimum, the query expects these table names to exist:

```text
commitments.customer_promises
linear.issues
github.pulls
slack.messages
intercom.conversations
stripe.invoices
launchdarkly.feature_flags
```

Then run:

```bash
COMMITMENT_RADAR_MODE=coral python run.py
```

PowerShell:

```powershell
$env:COMMITMENT_RADAR_MODE = "coral"
python run.py
```

You can also run the Coral query directly:

```bash
coral sql -f coral/queries/commitment_risk.sql --format json
```

## API Endpoints

```text
GET /api/health
```

Returns app mode, Coral command, source table names, and data provenance.

```text
GET /api/risks
```

Returns ranked commitment-risk rows.

```text
GET /api/evidence/<feature_key>
```

Returns a single commitment with an explanation and recommended action.

```text
GET /api/coral-query
```

Returns the SQL query that live Coral mode executes.

## Deployment

This repo includes Docker and Render support:

```text
Dockerfile
render.yaml
requirements.txt
```

The included Render configuration deploys demo mode by default:

```text
COMMITMENT_RADAR_MODE=demo
```

That is intentional for a public deployment. To deploy live Coral mode, the runtime also needs the Coral CLI and real source credentials configured as deployment secrets.

## Project Structure

```text
backend/
  app_server.py          HTTP server and API routes
  coral_client.py        Live Coral CLI wrapper
  demo_engine.py         Sample CSV join engine for public demo mode
  explainer.py           Evidence explanation and recommended action
  risk.py                Risk scoring and ranking

coral/
  queries/
    commitment_risk.sql  Main cross-source Coral query
    evidence_pack.sql    Supporting evidence query
    blocker_scan.sql     Slack blocker query
  source_specs/
    customer_promises.example.yml

data/demo/               Sample dataset used by demo mode
static/                  Browser dashboard
```

## What This Project Is Not

This is not a static dashboard with Coral branding pasted on top. The live path is a real `coral sql` execution path.

This is also not claiming that the public deployment has access to private production accounts. The public deployment uses sample data so the product can be tested safely.

The important architecture is:

```text
Coral SQL joins cross-source data
-> backend ranks and explains risk
-> dashboard shows evidence and action
```
