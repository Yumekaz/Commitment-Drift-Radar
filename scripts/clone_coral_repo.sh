#!/usr/bin/env bash
set -euo pipefail

mkdir -p vendor

if [ -d vendor/coral/.git ]; then
  echo "vendor/coral already exists. Pulling latest..."
  git -C vendor/coral pull --ff-only
else
  git clone https://github.com/withcoral/coral vendor/coral
fi

echo "Coral repo is available at vendor/coral"
