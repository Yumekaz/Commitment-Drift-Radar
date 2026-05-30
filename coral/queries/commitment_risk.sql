-- Commitment Drift Radar: main Coral query
--
-- This is the core product query. In live mode the backend runs:
--
--   coral sql -f coral/queries/commitment_risk.sql --format json
--
-- Coral owns the cross-source retrieval layer here. The app does not call
-- GitHub, Linear, Slack, Intercom, Stripe, or LaunchDarkly APIs directly.
--
-- Question answered:
--   "Which customer promises are drifting away from engineering reality?"
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
-- Adjust exact table/column names after running:
--   coral sql "SELECT schema_name, table_name FROM coral.tables ORDER BY 1, 2"

-- Intercom support pressure by customer account.
WITH support_pressure AS (
  SELECT
    company_id,
    COUNT(*) AS open_tickets,
    MAX(updated_at) AS last_support_touch,
    MAX(subject) AS latest_support_subject
  FROM intercom.conversations
  WHERE state = 'open'
  GROUP BY company_id
),

-- Stripe revenue makes risk prioritization business-aware.
revenue AS (
  SELECT
    customer_id,
    SUM(amount_paid) / 100.0 AS paid_last_90_days
  FROM stripe.invoices
  WHERE status = 'paid'
  GROUP BY customer_id
),

-- Slack blocker language is noisy, but useful as supporting evidence.
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

-- GitHub PRs are matched through the Linear/Jira key or feature key.
pull_requests AS (
  SELECT
    repo,
    title,
    head_ref,
    merged_at,
    html_url
  FROM github.pulls
),

-- LaunchDarkly flag state proves whether "done" reached the customer.
-- If your Coral LaunchDarkly source exposes a different rollout table, keep
-- this CTE name and adapt only the SELECT below.
rollout AS (
  SELECT
    feature_key,
    customer_name,
    CASE
      WHEN LOWER(CAST(enabled_for_customer AS VARCHAR)) IN ('true', '1', 'yes') THEN 'true'
      ELSE 'false'
    END AS rollout_enabled
  FROM launchdarkly.feature_flags
  WHERE environment = 'production'
)

SELECT
  -- Customer promise ledger.
  c.customer_name,
  c.feature_key,
  c.feature_name,
  c.promised_date,
  c.linear_issue_key,
  c.github_repo,

  -- Joined engineering, revenue, support, Slack, PR, and rollout evidence.
  li.state AS engineering_status,
  COALESCE(r.paid_last_90_days, 0) AS paid_last_90_days,
  COALESCE(sp.open_tickets, 0) AS open_tickets,
  sp.latest_support_subject,
  COALESCE(b.blocker_count, 0) AS blocker_count,
  b.latest_blocker,
  MAX(p.merged_at) AS latest_merged_pr,
  MAX(p.html_url) AS pr_url,
  COALESCE(ro.rollout_enabled, 'false') AS rollout_enabled,

  -- Risk label from joined evidence. The backend adds a numeric risk_score.
  CASE
    WHEN c.promised_date < CURRENT_DATE
      AND (
        li.state IS NULL
        OR LOWER(li.state) NOT IN ('done', 'completed', 'closed')
        OR MAX(p.merged_at) IS NULL
        OR COALESCE(ro.rollout_enabled, 'false') <> 'true'
      )
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

-- Source 1: Linear/Jira engineering state.
LEFT JOIN linear.issues li
  ON li.identifier = c.linear_issue_key

-- Source 2: GitHub implementation proof.
LEFT JOIN pull_requests p
  ON p.repo = c.github_repo
 AND (
      LOWER(p.title) LIKE '%' || LOWER(c.linear_issue_key) || '%'
      OR LOWER(p.head_ref) LIKE '%' || LOWER(c.linear_issue_key) || '%'
      OR LOWER(p.title) LIKE '%' || LOWER(c.feature_key) || '%'
      OR LOWER(p.head_ref) LIKE '%' || LOWER(c.feature_key) || '%'
 )

-- Source 3: Stripe revenue impact.
LEFT JOIN revenue r
  ON r.customer_id = c.stripe_customer_id

-- Source 4: Intercom customer pressure.
LEFT JOIN support_pressure sp
  ON sp.company_id = c.intercom_company_id

-- Source 5: Slack blocker evidence.
LEFT JOIN blockers b
  ON b.channel = c.slack_channel

-- Source 6: LaunchDarkly rollout reality.
LEFT JOIN rollout ro
  ON ro.feature_key = c.feature_key
 AND ro.customer_name = c.customer_name

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
  sp.latest_support_subject,
  b.blocker_count,
  b.latest_blocker,
  ro.rollout_enabled

ORDER BY
  risk_level DESC,
  paid_last_90_days DESC,
  promised_date ASC;
