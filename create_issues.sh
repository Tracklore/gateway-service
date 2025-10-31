#!/bin/bash

# Create issues for gateway-service

# Function to create an issue
create_issue() {
    local title=$1
    local body=$2
    local labels=$3
    
    echo "Creating issue: $title"
    gh issue create --title "$title" --body "$body" --label "$labels"
}

# Function to create a label if it doesn't exist
create_label() {
    local label_name=$1
    local label_color=$2
    local label_desc=$3
    
    # Check if label exists
    if ! gh label list | grep -q "^$label_name"; then
        echo "Creating label: $label_name"
        gh label create "$label_name" --color "$label_color" --description "$label_desc"
    else
        echo "Label $label_name already exists"
    fi
}

# Create labels
create_label "security" "e11d21" "Security related issues"
create_label "enhancement" "a2eeef" "New feature or request"
create_label "monitoring" "5319e7" "Monitoring and observability improvements"
create_label "configuration" "c5def5" "Configuration related issues"

# Create issues
create_issue "Restrict CORS configuration" "Update CORS configuration to restrict origins to specific allowed domains rather than allowing all. Security improvement to prevent unauthorized cross-origin requests." "security,enhancement"
create_issue "Implement comprehensive health checks" "Enhance the health check endpoint to include more detailed information about service dependencies and status. Add monitoring for downstream service connectivity." "monitoring,enhancement"
create_issue "Add request/response logging" "Implement detailed logging for all proxied requests and responses for debugging and monitoring purposes. Include correlation IDs for request tracing." "monitoring,enhancement"

echo "All issues created for gateway-service!"