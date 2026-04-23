#!/bin/bash
# Monitor the Product Collection log file in real-time
# Usage: bash monitor_products.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/log"
LOG_FILE="$LOG_DIR/product_collection.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo ""
    echo "To start processing in background, run:"
    echo "  bash run_product_with_nohup.sh"
    exit 1
fi

echo "=============================================================================="
echo "Monitoring Task 6: Product Information Collection Progress"
echo "=============================================================================="
echo ""
echo "Log file: $LOG_FILE"
echo "Press Ctrl+C to stop monitoring (process will continue running)"
echo ""
echo "Latest logs (last 50 lines):"
echo "—————————————————————————————————————————————————————————————————————————————"
echo ""

tail -f "$LOG_FILE"
