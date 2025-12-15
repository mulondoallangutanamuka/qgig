#!/bin/bash

# Real-Time Notification System - E2E Test Runner
# This script sets up and runs the complete E2E test

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Real-Time Notification System - E2E Test Runner         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if server is running
echo "[1/4] Checking if Flask server is running..."
if curl -s http://localhost:5000 > /dev/null; then
    echo "   ✓ Server is running on http://localhost:5000"
else
    echo "   ✗ Server is NOT running!"
    echo ""
    echo "   Please start the server first:"
    echo "   $ python main.py"
    echo ""
    exit 1
fi

# Check if pytest is installed
echo ""
echo "[2/4] Checking dependencies..."
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "   ✗ pytest not found!"
    echo "   Installing pytest and pytest-playwright..."
    pip install pytest pytest-playwright
fi

if ! python -m playwright --version > /dev/null 2>&1; then
    echo "   Installing Playwright browsers..."
    python -m playwright install
fi
echo "   ✓ Dependencies installed"

# Run the E2E test
echo ""
echo "[3/4] Running E2E test..."
echo "════════════════════════════════════════════════════════════"
echo ""

python -m pytest tests/test_realtime_notifications_e2e.py::test_realtime_notification_flow -v -s --tb=short

# Check test result
if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "[4/4] ✓✓✓ ALL TESTS PASSED! ✓✓✓"
    echo ""
    echo "Real-time notification system is working correctly!"
    echo ""
    echo "What was tested:"
    echo "  ✓ Institution posts a job"
    echo "  ✓ Professional shows interest"
    echo "  ✓ Institution receives notification in < 1 second"
    echo "  ✓ Notification appears in UI"
    echo "  ✓ Accept/Reject buttons work"
    echo "  ✓ Professional receives decision notification"
    echo ""
else
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "[4/4] ✗ TEST FAILED"
    echo ""
    echo "Check the output above for details."
    echo "Screenshots have been saved for debugging:"
    echo "  - test_failure_institution.png"
    echo "  - test_failure_professional.png"
    echo ""
    exit 1
fi

