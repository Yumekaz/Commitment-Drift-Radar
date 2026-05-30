#!/usr/bin/env bash
set -euo pipefail

echo "Discovering Coral bundled sources..."
coral source discover

echo "Adding required sources interactively..."
coral source add --interactive github
coral source add --interactive linear
coral source add --interactive slack
coral source add --interactive stripe
coral source add --interactive intercom
coral source add --interactive launchdarkly

echo "Now configure your customer commitments CSV/file source according to the current Coral file source docs."
echo "Then test tables with:"
echo '  coral sql "SELECT schema_name, table_name FROM coral.tables ORDER BY 1, 2"'
