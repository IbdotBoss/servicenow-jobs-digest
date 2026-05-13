#!/bin/bash
# Wrapper for ServiceNow Jobs Digest daily cron
cd /home/ubuntu/hermes-workspace/servicenow-jobs-digest
python3 daily_cron.py >> daily_cron.log 2>&1
