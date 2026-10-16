#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
node -e 'if(Number(process.versions.node.split(".")[0])<24){throw new Error("Node.js 24 ou superior é necessário")}'
npm ci --cache "${npm_config_cache:-.npm-cache}" --no-audit --no-fund
npm run build
npm test
# Preserve all existing data. Importing initial spreadsheets is a separate, explicit step.
# A retained data/seed.json initializes a missing SQLite database on first start.
