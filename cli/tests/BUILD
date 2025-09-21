python_sources(
    sources=["*.py"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#click",
        "//3rdparty/python:test_reqs#pyyaml",
    ],
)

python_tests(
    name="test_service_commands",
    sources=["test_service_commands.py"],
    tags=["unit", "cli"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#click",
    ],
)

python_tests(
    name="test_stack_commands",
    sources=["test_stack_commands.py"],
    tags=["unit", "cli"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#click",
        "//3rdparty/python:test_reqs#pyyaml",
    ],
)

python_tests(
    name="test_dev_commands",
    sources=["test_dev_commands.py"],
    tags=["unit", "cli"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#click",
    ],
)