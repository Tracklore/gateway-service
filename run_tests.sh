#!/bin/bash

# Test runner script for gateway-service
# This script runs all tests with different configurations

echo "========================================="
echo "Gateway Service Test Runner"
echo "========================================="

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "Installing test dependencies..."
    pip install pytest pytest-mock pytest-asyncio httpx pytest-cov
fi

# Check if tests directory exists
if [ ! -d "tests" ]; then
    echo "Error: tests directory not found!"
    exit 1
fi

# Function to run tests with coverage
run_tests_with_coverage() {
    echo "-----------------------------------------"
    echo "Running tests with coverage..."
    echo "-----------------------------------------"
    python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
}

# Function to run specific test suite
run_test_suite() {
    local suite_name=$1
    local suite_file=$2
    echo "-----------------------------------------"
    echo "Running $suite_name tests..."
    echo "-----------------------------------------"
    python -m pytest "$suite_file" -v
}

# Function to run tests in parallel
run_tests_parallel() {
    echo "-----------------------------------------"
    echo "Running tests in parallel..."
    echo "-----------------------------------------"
    python -m pytest tests/ -v -n auto
}

# Main menu
echo ""
echo "Select test option:"
echo "1. Run all tests"
echo "2. Run all tests with coverage"
echo "3. Run unit tests only"
echo "4. Run integration tests only"
echo "5. Run performance tests only"
echo "6. Run edge case tests only"
echo "7. Run authentication tests only"
echo "8. Run circuit breaker tests only"
echo "9. Run specific test file"
echo "10. Run tests in parallel"
echo "11. Exit"
echo ""

read -p "Enter your choice (1-11): " choice

case $choice in
    1)
        echo "Running all tests..."
        python -m pytest tests/ -v
        ;;
    2)
        run_tests_with_coverage
        ;;
    3)
        run_test_suite "unit" "tests/test_routes.py tests/test_auth.py"
        ;;
    4)
        run_test_suite "integration" "tests/test_integration.py"
        ;;
    5)
        run_test_suite "performance" "tests/test_performance.py"
        ;;
    6)
        run_test_suite "edge case" "tests/test_edge_cases.py"
        ;;
    7)
        run_test_suite "authentication" "tests/test_auth_utils.py tests/test_auth.py"
        ;;
    8)
        run_test_suite "circuit breaker" "tests/test_circuit_breaker.py"
        ;;
    9)
        read -p "Enter test file path: " test_file
        if [ -f "$test_file" ]; then
            echo "Running $test_file..."
            python -m pytest "$test_file" -v
        else
            echo "Error: File $test_file not found!"
        fi
        ;;
    10)
        run_tests_parallel
        ;;
    11)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Running all tests by default..."
        python -m pytest tests/ -v
        ;;
esac

echo ""
echo "Test run completed!"