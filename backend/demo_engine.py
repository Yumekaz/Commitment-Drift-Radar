import csv
from datetime import date, datetime
from pathlib import Path


class DemoEngine:
    """Local demo engine that simulates Coral's joined result using CSVs.

    This is only for local demos when credentials are unavailable.
    In live mode, use CoralClient instead.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    def read_csv(self, name):
        path = self.data_dir / name
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def compute_risk_rows(self):
        commitments = self.read_csv("commitments.csv")
        pulls = self.read_csv("github_pulls.csv")
        issues = self.read_csv("linear_issues.csv")
        slack = self.read_csv("slack_messages.csv")
        invoices = self.read_csv("stripe_invoices.csv")
        conversations = self.read_csv("intercom_conversations.csv")
        flags = self.read_csv("launchdarkly_flags.csv")

        rows = []
        today = date.today()

        for c in commitments:
            feature_key = c["feature_key"]
            linear_key = c["linear_issue_key"]

            issue = find_one(issues, "identifier", linear_key)
            matching_pulls = [
                p for p in pulls
                if p["repo"] == c["github_repo"]
                and (
                    linear_key.lower() in p["title"].lower()
                    or linear_key.lower() in p["head_ref"].lower()
                    or feature_key.lower() in p["title"].lower()
                    or feature_key.lower() in p["head_ref"].lower()
                )
            ]

            merged = [p for p in matching_pulls if p.get("merged_at")]
            latest_merged_pr = max((p["merged_at"] for p in merged), default="")
            pr_url = next((p["html_url"] for p in merged if p["merged_at"] == latest_merged_pr), "")

            support = [
                s for s in conversations
                if s["company_id"] == c["intercom_company_id"] and s["state"] == "open"
            ]

            blocker_msgs = [
                m for m in slack
                if m["channel"] == c["slack_channel"]
                and any(word in m["text"].lower() for word in ["blocked", "stuck", "risk", "delay", "waiting"])
            ]

            customer_invoices = [
                inv for inv in invoices
                if inv["customer_id"] == c["stripe_customer_id"] and inv["status"] == "paid"
            ]
            paid_last_90_days = sum(float(inv["amount_paid"]) / 100 for inv in customer_invoices)

            flag = find_one(flags, "feature_key", feature_key)
            promised_date = parse_date(c["promised_date"])

            risk_level = calculate_level(
                promised_date=promised_date,
                today=today,
                issue_state=(issue or {}).get("state", ""),
                latest_merged_pr=latest_merged_pr,
                open_tickets=len(support),
                blocker_count=len(blocker_msgs),
                rollout_enabled=(flag or {}).get("enabled_for_customer", "false").lower() == "true",
            )

            rows.append({
                "customer_name": c["customer_name"],
                "feature_key": feature_key,
                "feature_name": c["feature_name"],
                "promised_date": c["promised_date"],
                "linear_issue_key": linear_key,
                "engineering_status": (issue or {}).get("state", "unknown"),
                "github_repo": c["github_repo"],
                "latest_merged_pr": latest_merged_pr,
                "pr_url": pr_url,
                "open_tickets": len(support),
                "latest_support_subject": max((s["subject"] for s in support), default=""),
                "blocker_count": len(blocker_msgs),
                "latest_blocker": blocker_msgs[-1]["text"] if blocker_msgs else "",
                "paid_last_90_days": round(paid_last_90_days, 2),
                "rollout_enabled": (flag or {}).get("enabled_for_customer", "unknown"),
                "risk_level": risk_level,
            })

        return rows


def find_one(rows, key, value):
    return next((r for r in rows if r.get(key) == value), None)


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def calculate_level(promised_date, today, issue_state, latest_merged_pr, open_tickets, blocker_count, rollout_enabled):
    overdue = promised_date < today
    issue_not_done = issue_state.lower() not in {"done", "completed", "closed"}
    not_merged = not latest_merged_pr

    if overdue and (issue_not_done or not_merged or not rollout_enabled):
        return "CRITICAL"
    if not_merged and (open_tickets >= 2 or blocker_count >= 1):
        return "HIGH"
    if issue_not_done or open_tickets >= 2 or not rollout_enabled:
        return "MEDIUM"
    return "LOW"
