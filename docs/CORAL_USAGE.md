# Coral Usage

This document explains exactly where Coral fits in Commitment Drift Radar.

## Short Version

Coral is the live retrieval layer.

In live mode, the app runs:

```bash
coral sql -f coral/queries/commitment_risk.sql --format json
```

The app then ranks and explains the rows returned by Coral.

## Why Coral Is Useful Here

The product needs evidence from several systems at once:

- a customer promise ledger
- Linear or Jira engineering issues
- GitHub pull requests
- Slack blocker messages
- Intercom support tickets
- Stripe revenue
- LaunchDarkly rollout flags

Without Coral, the backend would need separate API clients, auth flows, pagination logic, caching, and join logic for every provider.

With Coral, those sources are queried as SQL tables. The main product logic can be expressed as one cross-source SQL query.

## The Core Query

The main query is:

```text
coral/queries/commitment_risk.sql
```

It joins:

| Source | Table |
| --- | --- |
| Customer commitments | `commitments.customer_promises` |
| Engineering issues | `linear.issues` |
| Pull requests | `github.pulls` |
| Blocker messages | `slack.messages` |
| Support tickets | `intercom.conversations` |
| Revenue | `stripe.invoices` |
| Feature flags | `launchdarkly.feature_flags` |

The query outputs one row per customer commitment with fields such as:

- `customer_name`
- `feature_name`
- `promised_date`
- `engineering_status`
- `latest_merged_pr`
- `open_tickets`
- `latest_blocker`
- `paid_last_90_days`
- `rollout_enabled`
- `risk_level`

## Live Mode

Live mode is enabled with:

```bash
COMMITMENT_RADAR_MODE=coral python run.py
```

PowerShell:

```powershell
$env:COMMITMENT_RADAR_MODE = "coral"
python run.py
```

When this mode is active, `backend/coral_client.py` executes the Coral CLI command and parses the JSON result.

If Coral is not installed, or if the required sources are not configured, the API returns a clear error. It does not silently report sample results as live Coral output.

## Demo Mode

Demo mode is enabled by default:

```bash
python run.py
```

It reads sample CSV files from:

```text
data/demo/
```

Demo mode exists so the public app can be opened without private source credentials. It is a sample-data simulation of the joined result shape that live Coral mode returns.

The dashboard labels this clearly as:

```text
DEMO MODE / SAMPLE DATA
```

It also shows:

- current data mode
- the Coral command
- the source table list
- a `Show SQL joins` button

## What Is Honest To Claim

Accurate:

```text
The live data path is built around the official Coral CLI.
The public deployment uses sample CSV data for safe review.
The app exposes the exact Coral SQL query used by live mode.
```

Not accurate:

```text
The public deployment is currently pulling live GitHub, Slack, Stripe,
Intercom, Linear, and LaunchDarkly data.
```

That would only be true after configuring Coral sources and running:

```text
COMMITMENT_RADAR_MODE=coral
```

## Backend Flow

```text
Demo mode:
data/demo/*.csv
-> DemoEngine
-> risk scoring
-> API
-> dashboard
```

```text
Live Coral mode:
coral sql -f coral/queries/commitment_risk.sql --format json
-> CoralClient
-> risk scoring
-> API
-> dashboard
```

## How The Live Path Is Implemented

The live path is implemented in code:

```text
backend/coral_client.py
```

That file shells out to:

```bash
coral sql -f coral/queries/commitment_risk.sql --format json
```

The backend does not contain provider-specific GitHub, Slack, Stripe, Intercom, Linear, or LaunchDarkly API clients. Coral is the intended system that owns the cross-source retrieval and SQL join layer.
