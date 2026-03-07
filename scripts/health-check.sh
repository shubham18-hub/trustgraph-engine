#!/bin/bash
# TrustGraph Engine - Health Check Script
# Monitors system health and sends alerts

set -e

# Configuration
API_ENDPOINT="${API_ENDPOINT:-http://localhost:8000}"
ALERT_EMAIL="${ALERT_EMAIL:-ops@trustgraph.gov.in}"
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "TrustGraph Engine - Health Check"
echo "=========================================="
echo "Endpoint: $API_ENDPOINT"
echo "Time: $(date)"
echo "=========================================="

# Initialize status
OVERALL_STATUS="healthy"
FAILED_CHECKS=()

# Function to check endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Checking $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10)
    
    if [ "$response" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response)"
        FAILED_CHECKS+=("$name")
        OVERALL_STATUS="unhealthy"
        return 1
    fi
}

# Function to check service
check_service() {
    local name=$1
    local command=$2
    
    echo -n "Checking $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED_CHECKS+=("$name")
        OVERALL_STATUS="unhealthy"
        return 1
    fi
}

# API Health Checks
echo ""
echo "API Health Checks:"
check_endpoint "Health Endpoint" "$API_ENDPOINT/api/health"
check_endpoint "Auth Service" "$API_ENDPOINT/api/auth/health"
check_endpoint "Voice Service" "$API_ENDPOINT/api/voice/health"
check_endpoint "Wallet Service" "$API_ENDPOINT/api/wallet/health"

# Database Check
echo ""
echo "Database Checks:"
if [ -f "/app/data/trustgraph.db" ]; then
    db_size=$(du -h /app/data/trustgraph.db | cut -f1)
    echo -e "Database size: ${GREEN}$db_size${NC}"
    
    # Check if database is writable
    if [ -w "/app/data/trustgraph.db" ]; then
        echo -e "Database writable: ${GREEN}✓ YES${NC}"
    else
        echo -e "Database writable: ${RED}✗ NO${NC}"
        FAILED_CHECKS+=("Database Write Permission")
        OVERALL_STATUS="unhealthy"
    fi
else
    echo -e "Database file: ${RED}✗ NOT FOUND${NC}"
    FAILED_CHECKS+=("Database File")
    OVERALL_STATUS="unhealthy"
fi

# Disk Space Check
echo ""
echo "System Resources:"
disk_usage=$(df -h /app | tail -1 | awk '{print $5}' | sed 's/%//')
echo -n "Disk usage: "
if [ "$disk_usage" -lt 80 ]; then
    echo -e "${GREEN}${disk_usage}%${NC}"
elif [ "$disk_usage" -lt 90 ]; then
    echo -e "${YELLOW}${disk_usage}% (Warning)${NC}"
else
    echo -e "${RED}${disk_usage}% (Critical)${NC}"
    FAILED_CHECKS+=("Disk Space")
    OVERALL_STATUS="unhealthy"
fi

# Memory Check
memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
echo -n "Memory usage: "
if [ "$memory_usage" -lt 80 ]; then
    echo -e "${GREEN}${memory_usage}%${NC}"
elif [ "$memory_usage" -lt 90 ]; then
    echo -e "${YELLOW}${memory_usage}% (Warning)${NC}"
else
    echo -e "${RED}${memory_usage}% (Critical)${NC}"
    FAILED_CHECKS+=("Memory Usage")
    OVERALL_STATUS="unhealthy"
fi

# Process Check
echo ""
echo "Process Checks:"
if pgrep -f "uvicorn" > /dev/null; then
    process_count=$(pgrep -f "uvicorn" | wc -l)
    echo -e "Uvicorn processes: ${GREEN}$process_count running${NC}"
else
    echo -e "Uvicorn processes: ${RED}✗ NOT RUNNING${NC}"
    FAILED_CHECKS+=("Uvicorn Process")
    OVERALL_STATUS="unhealthy"
fi

# AWS Services Check (if in production)
if [ "$ENVIRONMENT" = "production" ]; then
    echo ""
    echo "AWS Services:"
    
    # Check AWS credentials
    if aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "AWS credentials: ${GREEN}✓ VALID${NC}"
    else
        echo -e "AWS credentials: ${RED}✗ INVALID${NC}"
        FAILED_CHECKS+=("AWS Credentials")
        OVERALL_STATUS="unhealthy"
    fi
fi

# Summary
echo ""
echo "=========================================="
if [ "$OVERALL_STATUS" = "healthy" ]; then
    echo -e "Overall Status: ${GREEN}✓ HEALTHY${NC}"
    exit 0
else
    echo -e "Overall Status: ${RED}✗ UNHEALTHY${NC}"
    echo ""
    echo "Failed checks:"
    for check in "${FAILED_CHECKS[@]}"; do
        echo "  - $check"
    done
    
    # Send alert
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"🚨 TrustGraph Health Check Failed\n\nFailed checks: ${FAILED_CHECKS[*]}\"}" \
            > /dev/null 2>&1
    fi
    
    exit 1
fi
