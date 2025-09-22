python_sources(
    name="api_core",
    sources=["domain/**/*.py", "adapters/**/*.py", "public/**/*.py"],
    resolve="api_main",  # Use api_main resolve for all API service components
    dependencies=[
        "//shared/core:core@resolve=api_main",
        "//shared/utils:utils@resolve=api_main",
        "//3rdparty/python:api_main_reqs",
    ],
)

python_sources(
    name="api_app",
    sources=["app/**/*.py"],
    resolve="api_main",
    dependencies=[
        ":api_core",
        "//shared/core:core@resolve=api_main",
        "//3rdparty/python:api_main_reqs",
    ],
)

python_tests(
    name="unit",
    sources=["tests/unit/**/*.py"],
    resolve="test",
    dependencies=[
        ":api_core",
        ":api_app",
    ],
)

python_tests(
    name="integration",
    sources=["tests/integration/**/*.py"],
    resolve="test",
    dependencies=[
        ":api_core",
        ":api_app",
    ],
)
