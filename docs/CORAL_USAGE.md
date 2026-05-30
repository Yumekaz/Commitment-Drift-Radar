# Coral Usage

This project is designed to make Coral the core technical piece.

## What Coral does here

Coral is responsible for joining data from:

- `commitments.customer_promises`
- `linear.issues`
- `github.pulls`
- `slack.messages`
- `intercom.conversations`
- `stripe.invoices`
- `launchdarkly.feature_flags`

The main query is:

```text
coral/queries/commitment_risk.sql
```

The app's live mode calls:

```bash
coral sql -f coral/queries/commitment_risk.sql --format json
```

## Demo mode vs live mode

Demo mode exists only because reviewers may not have your private API credentials.

- Demo mode: uses local CSV data to show the product experience.
- Live mode: calls the real Coral CLI.

## Why this is not fake Coral usage

The production path is not:

```text
Backend manually calls GitHub API + Slack API + Stripe API.
```

The production path is:

```text
Backend -> coral sql -> joined result -> dashboard/agent explanation.
```

That means Coral handles the cross-source retrieval and SQL correlation.
