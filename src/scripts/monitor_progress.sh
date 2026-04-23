#!/bin/bash
# Monitor the IP Location Processor log file in real-time
# Usage: bash monitor_progress.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/log"
LOG_FILE="$LOG_DIR/ip_processing.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo ""
    echo "To start processing in background, run:"
    echo "  bash run_with_nohup.sh"
    exit 1
fi

echo "=============================================================================="
echo "Monitoring IP Location Processor Progress"
echo "=============================================================================="
echo ""
echo "Log file: $LOG_FILE"
echo "Press Ctrl+C to stop monitoring (process will continue running)"
echo ""
echo "Latest logs (last 50 lines):"
echo "—————————————————————————————————————————————————————————————————————————————"
echo ""

tail -f "$LOG_FILE"
