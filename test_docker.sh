#!/bin/bash

# Test script for running tests inside the Docker container

# Build the Docker image
echo "Building Docker image..."
docker build -t gateway-service-test .

# Run tests inside the Docker container
echo "Running tests inside Docker container..."
docker run --rm gateway-service-test python -m pytest tests/ -v

echo "Docker tests completed!"