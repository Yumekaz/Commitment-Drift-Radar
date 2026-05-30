def explain_row(row):
    reasons = []

    if row.get("promised_date"):
        reasons.append(f"Promised date: {row['promised_date']}.")

    status = row.get("engineering_status")
    if status and status.lower() not in {"done", "completed", "closed"}:
        reasons.append(f"Engineering ticket {row.get('linear_issue_key')} is still {status}.")

    if not row.get("latest_merged_pr"):
        reasons.append("No merged pull request was found for this commitment.")
    else:
        reasons.append(f"Latest merged PR: {row['latest_merged_pr']}.")

    open_tickets = int(row.get("open_tickets") or 0)
    if open_tickets:
        reasons.append(f"There are {open_tickets} open support conversations.")

    blocker_count = int(row.get("blocker_count") or 0)
    if blocker_count:
        reasons.append(f"{blocker_count} recent blocker message(s) were found in Slack.")

    if str(row.get("rollout_enabled", "")).lower() == "false":
        reasons.append("The feature flag is not enabled for the customer.")

    revenue = float(row.get("paid_last_90_days") or 0)
    if revenue:
        reasons.append(f"Customer paid ${revenue:,.0f} in the sample revenue window.")

    return {
        "summary": f"{row.get('customer_name')} / {row.get('feature_name')} is {row.get('risk_level')} risk.",
        "reasons": reasons,
        "recommended_action": recommended_action(row),
    }


def recommended_action(row):
    level = str(row.get("risk_level", "LOW")).upper()

    if level == "CRITICAL":
        return "Escalate today: assign an owner, verify PR/deploy/flag state, and send a customer-facing update."
    if level == "HIGH":
        return "Review in standup: unblock engineering and confirm whether the promise date is still realistic."
    if level == "MEDIUM":
        return "Track closely: ask the owner to update the ticket and verify rollout status."
    return "No immediate escalation needed; keep monitoring."
