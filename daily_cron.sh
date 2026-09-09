#!/bin/bash
# Wrapper for ServiceNow Jobs Digest daily cron
# FIX: cron runs with minimal PATH — use the hermes venv python3 which has
# playwright + browser_cookie3 + requests installed.
export PATH="/home/ubuntu/.hermes/hermes-agent/venv/bin:$PATH"
cd /home/ubuntu/hermes-workspace/servicenow-jobs-digest
python3 daily_cron.py >> daily_cron.log 2>&1
