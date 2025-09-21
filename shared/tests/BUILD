python_sources(
    sources=["*.py"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#boto3",
        "//3rdparty/python:test_reqs#moto",
    ],
)

python_tests(
    name="test_aws_factory",
    sources=["test_aws_factory.py"],
    tags=["unit", "aws"],
    resolve="test",
)

python_tests(
    name="test_environment",
    sources=["test_environment.py"],
    tags=["unit", "config"],
    resolve="test",
)

python_tests(
    name="test_container",
    sources=["test_container.py"],
    tags=["unit", "di"],
    resolve="test",
)

python_tests(
    name="test_logging",
    sources=["test_logging.py"],
    tags=["unit", "logging"],
    resolve="test",
)