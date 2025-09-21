python_sources(
    name="api_core",
    sources=["domain/**/*.py", "adapters/**/*.py", "public/**/*.py"],
    resolve="api_core",
    dependencies=[
        "shared",
        "stack/libs/shared",
        "3rdparty/python:api_core_reqs",
    ],
)

python_sources(
    name="api_app",
    sources=["app/**/*.py"],
    resolve="api_main",
    dependencies=[
        ":api_core",
        "shared",
        "3rdparty/python:api_main_reqs",
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