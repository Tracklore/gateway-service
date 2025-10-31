#!/bin/bash

# Script to run the gateway-service with virtual environment activated

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
    touch .venv/installed
fi

# Run the service
echo "Starting gateway service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000