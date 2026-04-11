#!/bin/bash
# 每天北京时间 10:00 发送 Nasdaq_ai_trader 日志到飞书

LOG_FILE="/Users/zz/Nasdaq_ai_trader/logs/trading.log"

# 获取最后 50 行日志
TAIL_CONTENT=$(tail -50 "$LOG_FILE")

# 通过 OpenClaw message 工具发送（需要在运行后手动读取内容）

# 同时保存到文件备份
echo "$TAIL_CONTENT" > /Users/zz/Nasdaq_ai_trader/logs/latest_trading_log.txt

echo "日志已保存: $(date)"
echo "$TAIL_CONTENT"