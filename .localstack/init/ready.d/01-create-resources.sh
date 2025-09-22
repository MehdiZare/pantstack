#!/bin/bash
# LocalStack initialization script - Create AWS resources
# This script runs automatically when LocalStack is ready

set -e

echo "🚀 Initializing LocalStack resources..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# DynamoDB Tables
echo -e "${YELLOW}Creating DynamoDB tables...${NC}"

# Auth service - Users table
awslocal dynamodb create-table \
  --table-name auth-users-dev \
  --attribute-definitions \
    AttributeName=userId,AttributeType=S \
    AttributeName=email,AttributeType=S \
  --key-schema \
    AttributeName=userId,KeyType=HASH \
  --global-secondary-indexes \
    "IndexName=EmailIndex,Keys=[{AttributeName=email,KeyType=HASH}],Projection={ProjectionType=ALL},BillingMode=PAY_PER_REQUEST" \
  --billing-mode PAY_PER_REQUEST \
  2>/dev/null || echo "Table auth-users-dev already exists"

# Auth service - Sessions table
awslocal dynamodb create-table \
  --table-name auth-sessions-dev \
  --attribute-definitions \
    AttributeName=sessionId,AttributeType=S \
    AttributeName=userId,AttributeType=S \
  --key-schema \
    AttributeName=sessionId,KeyType=HASH \
  --global-secondary-indexes \
    "IndexName=UserIdIndex,Keys=[{AttributeName=userId,KeyType=HASH}],Projection={ProjectionType=KEYS_ONLY},BillingMode=PAY_PER_REQUEST" \
  --billing-mode PAY_PER_REQUEST \
  2>/dev/null || echo "Table auth-sessions-dev already exists"

echo -e "${GREEN}✓ DynamoDB tables created${NC}"

# S3 Buckets
echo -e "${YELLOW}Creating S3 buckets...${NC}"

awslocal s3 mb s3://pantstack-uploads-dev 2>/dev/null || echo "Bucket pantstack-uploads-dev already exists"
awslocal s3 mb s3://pantstack-assets-dev 2>/dev/null || echo "Bucket pantstack-assets-dev already exists"
awslocal s3 mb s3://pantstack-backups-dev 2>/dev/null || echo "Bucket pantstack-backups-dev already exists"

# Set bucket policies
awslocal s3api put-bucket-cors \
  --bucket pantstack-uploads-dev \
  --cors-configuration '{
    "CORSRules": [{
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["http://localhost:3000", "http://localhost:8000"],
      "MaxAgeSeconds": 3000
    }]
  }' 2>/dev/null || true

echo -e "${GREEN}✓ S3 buckets created${NC}"

# SQS Queues
echo -e "${YELLOW}Creating SQS queues...${NC}"

# Main queue with DLQ
awslocal sqs create-queue \
  --queue-name pantstack-dlq-dev \
  --attributes MessageRetentionPeriod=1209600 \
  2>/dev/null || echo "Queue pantstack-dlq-dev already exists"

DLQ_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/pantstack-dlq-dev \
  --attribute-names QueueArn \
  --output text --query 'Attributes.QueueArn')

awslocal sqs create-queue \
  --queue-name pantstack-main-dev \
  --attributes "{
    \"MessageRetentionPeriod\": \"345600\",
    \"VisibilityTimeout\": \"300\",
    \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":3}\"
  }" 2>/dev/null || echo "Queue pantstack-main-dev already exists"

# Service-specific queues
awslocal sqs create-queue --queue-name auth-queue-dev 2>/dev/null || echo "Queue auth-queue-dev already exists"
awslocal sqs create-queue --queue-name notifications-queue-dev 2>/dev/null || echo "Queue notifications-queue-dev already exists"

echo -e "${GREEN}✓ SQS queues created${NC}"

# EventBridge
echo -e "${YELLOW}Creating EventBridge resources...${NC}"

# Create custom event bus
awslocal events create-event-bus \
  --name pantstack-events-dev \
  2>/dev/null || echo "Event bus pantstack-events-dev already exists"

# Create event rules
awslocal events put-rule \
  --name user-events-dev \
  --event-bus-name pantstack-events-dev \
  --event-pattern '{
    "source": ["auth.service"],
    "detail-type": ["User Registered", "User Updated", "User Deleted"]
  }' \
  --state ENABLED \
  2>/dev/null || echo "Rule user-events-dev already exists"

echo -e "${GREEN}✓ EventBridge configured${NC}"

# SSM Parameter Store
echo -e "${YELLOW}Creating SSM parameters...${NC}"

# JWT secrets
awslocal ssm put-parameter \
  --name "/auth/dev/jwt-secret" \
  --value "local-development-jwt-secret-key" \
  --type "SecureString" \
  --overwrite \
  2>/dev/null || true

awslocal ssm put-parameter \
  --name "/auth/dev/jwt-refresh-secret" \
  --value "local-development-jwt-refresh-secret" \
  --type "SecureString" \
  --overwrite \
  2>/dev/null || true

# Database credentials
awslocal ssm put-parameter \
  --name "/shared/dev/db-url" \
  --value "postgresql://postgres:postgres@postgres:5432/pantstack" \
  --type "SecureString" \
  --overwrite \
  2>/dev/null || true

# API keys
awslocal ssm put-parameter \
  --name "/shared/dev/internal-api-key" \
  --value "local-internal-api-key" \
  --type "SecureString" \
  --overwrite \
  2>/dev/null || true

echo -e "${GREEN}✓ SSM parameters created${NC}"

# Lambda Functions (placeholders)
echo -e "${YELLOW}Creating Lambda function placeholders...${NC}"

# Create a simple Lambda function
echo 'def handler(event, context): return {"statusCode": 200, "body": "OK"}' > /tmp/lambda.py
(cd /tmp && zip lambda.zip lambda.py)

awslocal lambda create-function \
  --function-name auth-verify-token-dev \
  --runtime python3.11 \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --handler lambda.handler \
  --zip-file fileb:///tmp/lambda.zip \
  2>/dev/null || echo "Lambda auth-verify-token-dev already exists"

awslocal lambda create-function \
  --function-name auth-process-signup-dev \
  --runtime python3.11 \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --handler lambda.handler \
  --zip-file fileb:///tmp/lambda.zip \
  2>/dev/null || echo "Lambda auth-process-signup-dev already exists"

rm -f /tmp/lambda.py /tmp/lambda.zip

echo -e "${GREEN}✓ Lambda functions created${NC}"

# CloudWatch Log Groups
echo -e "${YELLOW}Creating CloudWatch log groups...${NC}"

awslocal logs create-log-group --log-group-name /ecs/auth-dev 2>/dev/null || true
awslocal logs create-log-group --log-group-name /ecs/celery-worker-dev 2>/dev/null || true
awslocal logs create-log-group --log-group-name /aws/lambda/auth-verify-token-dev 2>/dev/null || true

echo -e "${GREEN}✓ CloudWatch log groups created${NC}"

echo -e "${GREEN}✅ LocalStack initialization complete!${NC}"
echo "Resources created:"
echo "  - DynamoDB tables: auth-users-dev, auth-sessions-dev"
echo "  - S3 buckets: pantstack-uploads-dev, pantstack-assets-dev, pantstack-backups-dev"
echo "  - SQS queues: pantstack-main-dev (with DLQ), auth-queue-dev, notifications-queue-dev"
echo "  - EventBridge bus: pantstack-events-dev"
echo "  - SSM parameters: JWT secrets, DB credentials, API keys"
echo "  - Lambda functions: auth-verify-token-dev, auth-process-signup-dev"
echo "  - CloudWatch log groups"
