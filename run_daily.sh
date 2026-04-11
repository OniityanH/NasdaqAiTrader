#!/bin/bash
cd /Users/zz/Nasdaq_ai_trader
source venv/bin/activate
python main.py >> /Users/zz/Nasdaq_ai_trader/logs/cron_$(date +\%Y\%m\%d).log 2>&1
