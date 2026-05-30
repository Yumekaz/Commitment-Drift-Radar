RISK_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def normalize_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def score_row(row):
    level = str(row.get("risk_level", "LOW")).upper()
    score = RISK_ORDER.get(level, 1) * 20

    score += min(normalize_int(row.get("open_tickets")), 5) * 5
    score += min(normalize_int(row.get("blocker_count")), 4) * 6
    score += min(normalize_float(row.get("paid_last_90_days")) / 1000, 25)

    if str(row.get("rollout_enabled", "")).lower() == "false":
        score += 10

    return min(round(score, 1), 100.0)


def rank_rows(rows):
    enriched = []
    for row in rows:
        row = dict(row)
        row["risk_score"] = score_row(row)
        row["risk_level"] = str(row.get("risk_level", "LOW")).upper()
        enriched.append(row)

    return sorted(
        enriched,
        key=lambda r: (
            RISK_ORDER.get(r.get("risk_level", "LOW"), 0),
            normalize_float(r.get("risk_score")),
            normalize_float(r.get("paid_last_90_days")),
        ),
        reverse=True,
    )
