#!/bin/bash
# LocalStack initialization script - Seed test data
# This script runs automatically after resources are created

set -e

echo "🌱 Seeding test data..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Seed DynamoDB with test users
echo -e "${YELLOW}Seeding DynamoDB tables...${NC}"

# Test user 1
awslocal dynamodb put-item \
  --table-name auth-users-dev \
  --item '{
    "userId": {"S": "user-001"},
    "email": {"S": "admin@example.com"},
    "name": {"S": "Admin User"},
    "role": {"S": "admin"},
    "isActive": {"BOOL": true},
    "createdAt": {"S": "2024-01-01T00:00:00Z"}
  }' 2>/dev/null || true

# Test user 2
awslocal dynamodb put-item \
  --table-name auth-users-dev \
  --item '{
    "userId": {"S": "user-002"},
    "email": {"S": "user@example.com"},
    "name": {"S": "Test User"},
    "role": {"S": "user"},
    "isActive": {"BOOL": true},
    "createdAt": {"S": "2024-01-01T00:00:00Z"}
  }' 2>/dev/null || true

echo -e "${GREEN}✓ DynamoDB data seeded${NC}"

# Upload test files to S3
echo -e "${YELLOW}Uploading test files to S3...${NC}"

# Create test files
echo "Test asset content" > /tmp/test-asset.txt
echo '{"test": "data"}' > /tmp/test-data.json

# Upload to S3
awslocal s3 cp /tmp/test-asset.txt s3://pantstack-assets-dev/test/test-asset.txt 2>/dev/null || true
awslocal s3 cp /tmp/test-data.json s3://pantstack-uploads-dev/test/test-data.json 2>/dev/null || true

# Cleanup temp files
rm -f /tmp/test-asset.txt /tmp/test-data.json

echo -e "${GREEN}✓ S3 test files uploaded${NC}"

# Send test message to SQS
echo -e "${YELLOW}Sending test messages to SQS...${NC}"

awslocal sqs send-message \
  --queue-url http://localhost:4566/000000000000/pantstack-main-dev \
  --message-body '{
    "type": "test.message",
    "data": {
      "message": "LocalStack is ready!",
      "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
    }
  }' 2>/dev/null || true

echo -e "${GREEN}✓ SQS test message sent${NC}"

# Publish test event to EventBridge
echo -e "${YELLOW}Publishing test events to EventBridge...${NC}"

awslocal events put-events \
  --entries '[{
    "Source": "localstack.init",
    "DetailType": "System Ready",
    "Detail": "{\"message\": \"LocalStack initialized with test data\", \"timestamp\": \"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'\"}"
  }]' 2>/dev/null || true

echo -e "${GREEN}✓ EventBridge test event published${NC}"

echo -e "${GREEN}✅ Test data seeding complete!${NC}"
echo "Test data created:"
echo "  - Users: admin@example.com (admin), user@example.com (user)"
echo "  - S3 files: test-asset.txt, test-data.json"
echo "  - SQS message: Test message in main queue"
echo "  - EventBridge event: System Ready event"