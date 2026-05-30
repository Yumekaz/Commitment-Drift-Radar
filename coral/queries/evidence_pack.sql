-- Evidence pack query for one feature.
-- Replace :feature_key with the actual value or adapt for your SQL runner.

SELECT
  c.customer_name,
  c.feature_name,
  c.promised_date,
  c.linear_issue_key,
  li.state AS engineering_status,
  p.title AS pr_title,
  p.merged_at,
  p.html_url,
  sl.text AS slack_message,
  ic.subject AS support_subject
FROM commitments.customer_promises c
LEFT JOIN linear.issues li
  ON li.identifier = c.linear_issue_key
LEFT JOIN github.pulls p
  ON p.repo = c.github_repo
 AND (
      LOWER(p.title) LIKE '%' || LOWER(c.linear_issue_key) || '%'
      OR LOWER(p.head_ref) LIKE '%' || LOWER(c.linear_issue_key) || '%'
 )
LEFT JOIN slack.messages sl
  ON sl.channel = c.slack_channel
LEFT JOIN intercom.conversations ic
  ON ic.company_id = c.intercom_company_id
WHERE c.feature_key = :feature_key
ORDER BY ic.updated_at DESC, p.merged_at DESC;
