# Lambda function targets for auth service

python_sources(
    name="lambda_lib",
    sources=["*.py"],
    resolve="auth_lambda",
)

# Token verification Lambda (can be used as API Gateway authorizer)
python_aws_lambda_function(
    name="verify_token",
    handler="services.auth.src.lambdas.verify_token:handler",
    runtime="python3.11",
    dependencies=[
        ":lambda_lib",
        "3rdparty/python#pyjwt",
    ],
    resolve="auth_lambda",
    tags=["auth", "lambda"],
    description="JWT token verification Lambda for API Gateway authorization",
)

# User signup processing Lambda (triggered by SQS/EventBridge)
python_aws_lambda_function(
    name="process_signup",
    handler="services.auth.src.lambdas.process_signup:handler",
    runtime="python3.11",
    dependencies=[
        ":lambda_lib",
        "3rdparty/python#boto3",
    ],
    resolve="auth_lambda",
    tags=["auth", "lambda", "async"],
    description="Async user signup processing Lambda",
)

# Token refresh Lambda
python_aws_lambda_function(
    name="token_refresh",
    handler="services.auth.src.lambdas.token_refresh:handler",
    runtime="python3.11",
    dependencies=[
        ":lambda_lib",
        "3rdparty/python#pyjwt",
    ],
    resolve="auth_lambda",
    tags=["auth", "lambda"],
    description="JWT token refresh Lambda",
)

# Packaged Lambda deployment artifacts
python_aws_lambda_layer(
    name="auth_lambda_layer",
    dependencies=[
        "3rdparty/python#pyjwt",
        "3rdparty/python#boto3",
    ],
    resolve="auth_lambda",
    tags=["auth", "lambda", "layer"],
    description="Shared layer for auth Lambda functions",
)

# Archive targets for deployment
archive(
    name="verify_token_zip",
    packages=[":verify_token"],
    format="zip",
    tags=["auth", "lambda", "deploy"],
)

archive(
    name="process_signup_zip",
    packages=[":process_signup"],
    format="zip",
    tags=["auth", "lambda", "deploy"],
)

archive(
    name="token_refresh_zip",
    packages=[":token_refresh"],
    format="zip",
    tags=["auth", "lambda", "deploy"],
)