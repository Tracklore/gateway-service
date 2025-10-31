#!/bin/bash

# Script to run tests for the gateway-service with virtual environment activated

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python -m venv .venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies if requirements.txt is newer than installed packages
if [ requirements.txt -nt .venv/installed ]; then
    echo "Installing/updating dependencies..."
    pip install -r requirements.txt
fi

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-mock pytest-asyncio httpx

# Run the tests
echo "Running tests..."
exec pytest -v