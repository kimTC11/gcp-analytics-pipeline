#!/bin/bash
# Quick start script - Run this to get started
# Usage: bash quickstart.sh

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🚀 QUICK START - IP Location & Product Processing Pipeline"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /home/tuancuong112504/prj5-gcp

echo "Step 1: Verify Python environment..."
if [ -d ".venv" ]; then
    echo "✓ Python environment found"
else
    echo "✗ Python environment not found"
    exit 1
fi

echo ""
echo "Step 2: Running setup verification..."
python src/utils/test_setup.py

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📋 Next Steps:"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1. START TASK 5 (IP Location Processing):"
echo "   bash src/scripts/run_with_nohup.sh"
echo ""
echo "2. MONITOR PROGRESS:"
echo "   bash src/scripts/monitor_progress.sh"
echo ""
echo "3. WHEN TASK 5 COMPLETES, START TASK 6:"
echo "   bash src/scripts/run_product_with_nohup.sh"
echo ""
echo "4. VERIFY DATA QUALITY:"
echo "   python src/utils/verify_data_quality.py"
echo ""
echo "📚 For more information, read:"
echo "   INDEX.md              (Overview & structure)"
echo "   SETUP_GUIDE.md        (Installation)"
echo "   DATA_QUALITY.md       (Testing)"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
