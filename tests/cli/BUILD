python_sources(
    name="cli_test_lib",
    sources=["conftest.py", "cleanup.py"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#pytest",
        "//3rdparty/python:test_reqs#click",
        "//3rdparty/python:test_reqs#docker",
    ],
)

python_source(
    name="integration_runner",
    source="run_integration_tests.py",
    resolve="test",
)

python_tests(
    name="test_service_lifecycle",
    sources=["test_service_lifecycle.py"],
    tags=["integration", "cli"],
    resolve="test",
    dependencies=[
        ":cli_test_lib",
        "//3rdparty/python:test_reqs#pytest",
        "//scripts:new_service_script",  # Script dependency
    ],
    timeout=120,
    run_goal_use_sandbox=False,  # Need filesystem access for integration tests
)

python_tests(
    name="test_cleanup",
    sources=["test_cleanup_*.py"],
    tags=["unit", "cli"],
    resolve="test",
    dependencies=[
        ":cli_test_lib",
        "//3rdparty/python:test_reqs#pytest",
    ],
    timeout=60,
)

# Alternative runner for integration tests that need filesystem access
pex_binary(
    name="integration_test_runner",
    entry_point="run_integration_tests:main",
    resolve="test",
    dependencies=[
        ":integration_runner",
        ":test_service_lifecycle",
        ":cli_test_lib",
        "//3rdparty/python:test_reqs#pytest",
    ],
)