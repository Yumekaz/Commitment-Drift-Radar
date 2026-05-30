-- Commitment Drift Radar: main Coral query
-- Purpose:
--   Join customer promises with Linear, GitHub, Slack, Intercom, Stripe,
--   and LaunchDarkly to find commitments drifting away from reality.
--
-- Expected schemas:
--   commitments.customer_promises
--   linear.issues
--   github.pulls
--   slack.messages
--   intercom.conversations
--   stripe.invoices
--   launchdarkly.feature_flags
--
-- Adjust table/column names after running:
--   coral sql "SELECT schema_name, table_name FROM coral.tables ORDER BY 1, 2"

WITH support_pressure AS (
  SELECT
    company_id,
    COUNT(*) AS open_tickets,
    MAX(updated_at) AS last_support_touch
  FROM intercom.conversations
  WHERE state = 'open'
  GROUP BY company_id
),

revenue AS (
  SELECT
    customer_id,
    SUM(amount_paid) / 100.0 AS paid_last_90_days
  FROM stripe.invoices
  WHERE status = 'paid'
  GROUP BY customer_id
),

blockers AS (
  SELECT
    channel,
    COUNT(*) AS blocker_count,
    MAX(text) AS latest_blocker
  FROM slack.messages
  WHERE
    LOWER(text) LIKE '%blocked%'
    OR LOWER(text) LIKE '%stuck%'
    OR LOWER(text) LIKE '%delay%'
    OR LOWER(text) LIKE '%risk%'
    OR LOWER(text) LIKE '%waiting%'
  GROUP BY channel
),

pr_status AS (
  SELECT
    repo,
    title,
    head_ref,
    merged_at,
    html_url
  FROM github.pulls
),

rollout AS (
  SELECT
    key AS feature_key,
    CASE
      WHEN archived = false THEN 'unknown'
      ELSE 'unknown'
    END AS rollout_state
  FROM launchdarkly.feature_flags
)

SELECT
  c.customer_name,
  c.feature_key,
  c.feature_name,
  c.promised_date,
  c.linear_issue_key,
  c.github_repo,
  li.state AS engineering_status,
  r.paid_last_90_days,
  sp.open_tickets,
  b.blocker_count,
  b.latest_blocker,
  MAX(p.merged_at) AS latest_merged_pr,
  MAX(p.html_url) AS pr_url,
  COALESCE(ro.rollout_state, 'unknown') AS rollout_enabled,

  CASE
    WHEN c.promised_date < CURRENT_DATE
      AND (li.state IS NULL OR LOWER(li.state) NOT IN ('done', 'completed', 'closed') OR MAX(p.merged_at) IS NULL)
      THEN 'CRITICAL'
    WHEN MAX(p.merged_at) IS NULL
      AND (COALESCE(sp.open_tickets, 0) >= 2 OR COALESCE(b.blocker_count, 0) >= 1)
      THEN 'HIGH'
    WHEN li.state IS NULL
      OR LOWER(li.state) NOT IN ('done', 'completed', 'closed')
      OR COALESCE(sp.open_tickets, 0) >= 2
      THEN 'MEDIUM'
    ELSE 'LOW'
  END AS risk_level

FROM commitments.customer_promises c

LEFT JOIN linear.issues li
  ON li.identifier = c.linear_issue_key

LEFT JOIN pr_status p
  ON p.repo = c.github_repo
 AND (
      LOWER(p.title) LIKE '%' || LOWER(c.linear_issue_key) || '%'
      OR LOWER(p.head_ref) LIKE '%' || LOWER(c.linear_issue_key) || '%'
      OR LOWER(p.title) LIKE '%' || LOWER(c.feature_key) || '%'
      OR LOWER(p.head_ref) LIKE '%' || LOWER(c.feature_key) || '%'
 )

LEFT JOIN revenue r
  ON r.customer_id = c.stripe_customer_id

LEFT JOIN support_pressure sp
  ON sp.company_id = c.intercom_company_id

LEFT JOIN blockers b
  ON b.channel = c.slack_channel

LEFT JOIN rollout ro
  ON ro.feature_key = c.feature_key

GROUP BY
  c.customer_name,
  c.feature_key,
  c.feature_name,
  c.promised_date,
  c.linear_issue_key,
  c.github_repo,
  li.state,
  r.paid_last_90_days,
  sp.open_tickets,
  b.blocker_count,
  b.latest_blocker,
  ro.rollout_state

ORDER BY
  risk_level DESC,
  paid_last_90_days DESC,
  promised_date ASC;
