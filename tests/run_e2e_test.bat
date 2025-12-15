@echo off
REM Real-Time Notification System - E2E Test Runner (Windows)
REM This script sets up and runs the complete E2E test

echo ================================================================
echo    Real-Time Notification System - E2E Test Runner
echo ================================================================
echo.

REM Check if server is running
echo [1/4] Checking if Flask server is running...
curl -s http://localhost:5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo    √ Server is running on http://localhost:5000
) else (
    echo    X Server is NOT running!
    echo.
    echo    Please start the server first:
    echo    $ python main.py
    echo.
    exit /b 1
)

REM Check if pytest is installed
echo.
echo [2/4] Checking dependencies...
python -m pytest --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    X pytest not found!
    echo    Installing pytest and pytest-playwright...
    pip install pytest pytest-playwright
)

python -m playwright --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    Installing Playwright browsers...
    python -m playwright install
)
echo    √ Dependencies installed

REM Run the E2E test
echo.
echo [3/4] Running E2E test...
echo ================================================================
echo.

python -m pytest tests/test_realtime_notifications_e2e.py::test_realtime_notification_flow -v -s --tb=short

REM Check test result
if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo [4/4] √√√ ALL TESTS PASSED! √√√
    echo.
    echo Real-time notification system is working correctly!
    echo.
    echo What was tested:
    echo   √ Institution posts a job
    echo   √ Professional shows interest
    echo   √ Institution receives notification in ^< 1 second
    echo   √ Notification appears in UI
    echo   √ Accept/Reject buttons work
    echo   √ Professional receives decision notification
    echo.
) else (
    echo.
    echo ================================================================
    echo [4/4] X TEST FAILED
    echo.
    echo Check the output above for details.
    echo Screenshots have been saved for debugging:
    echo   - test_failure_institution.png
    echo   - test_failure_professional.png
    echo.
    exit /b 1
)

