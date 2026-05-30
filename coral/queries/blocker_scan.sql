-- Find promises with recent blocker language in Slack.

SELECT
  c.customer_name,
  c.feature_name,
  c.linear_issue_key,
  sl.created_at,
  sl.user,
  sl.text
FROM commitments.customer_promises c
JOIN slack.messages sl
  ON sl.channel = c.slack_channel
WHERE
  LOWER(sl.text) LIKE '%blocked%'
  OR LOWER(sl.text) LIKE '%stuck%'
  OR LOWER(sl.text) LIKE '%delay%'
  OR LOWER(sl.text) LIKE '%risk%'
  OR LOWER(sl.text) LIKE '%waiting%'
ORDER BY sl.created_at DESC;
