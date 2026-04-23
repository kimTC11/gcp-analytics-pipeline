#!/bin/bash
# Script to run Product Collection with nohup for background execution
# Usage: bash run_product_with_nohup.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
RUNNERS_DIR="$PROJECT_ROOT/src/runners"
VENV_DIR="$PROJECT_ROOT/.venv"
LOG_DIR="$PROJECT_ROOT/log"
LOG_FILE="$LOG_DIR/product_collection.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo "=============================================================================="
echo "Task 6: Product Information Collection - Background Execution with nohup"
echo "=============================================================================="
echo ""
echo "📝 Log file: $LOG_FILE"
echo "📊 PID will be displayed below (save it for monitoring/killing)"
echo "🔍 Monitor with: tail -f $LOG_FILE"
echo ""
echo "Starting process..."
echo ""

# Create virtual environment activation in the nohup command
cd "$RUNNERS_DIR"
nohup bash -c "source $VENV_DIR/bin/activate && python run_product_collection.py" > "$LOG_FILE" 2>&1 &

PID=$!
echo "✓ Process started with PID: $PID"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "Monitor the process:"
echo "  tail -f $LOG_FILE"
echo ""
echo "Check if process is still running:"
echo "  ps -p $PID"
echo ""
echo "Kill the process if needed:"
echo "  kill $PID"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Starting to show log output..."
echo ""

# Show the beginning of the log
sleep 2
tail -20 "$LOG_FILE"
