#!/bin/bash

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="/usr/bin/python3"  # Adjust if needed
DOWNLOAD_SCRIPT="$SCRIPT_DIR/download_and_process.py"
LOG_FILE="$SCRIPT_DIR/logs/download.log"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Retry until 8 AM or success
END_TIME=$(date -d "08:00" +%s)
CURRENT_TIME=$(date +%s)

while [ $CURRENT_TIME -lt $END_TIME ]; do
    echo "[$(date)] Attempting download..." >> "$LOG_FILE"
    $PYTHON_PATH "$DOWNLOAD_SCRIPT" >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[$(date)] Download succeeded. Stopping retries." >> "$LOG_FILE"
        exit 0
    fi
    echo "[$(date)] Download failed. Retrying in 15 minutes..." >> "$LOG_FILE"
    sleep 900  # 15 minutes
    CURRENT_TIME=$(date +%s)
done

echo "[$(date)] Reached 8 AM without successful download. Stopping." >> "$LOG_FILE"
exit 1