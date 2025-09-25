# Shared library for test resolve
python_sources(
    name="shared_test",
    sources=["**/*.py"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#boto3",
        "//3rdparty/python:test_reqs#redis",
        "//3rdparty/python:test_reqs#pydantic",
        "//3rdparty/python:test_reqs#pydantic-settings",
        "//3rdparty/python:test_reqs#pyyaml",
    ],
)

# Shared library for auth_core resolve
python_sources(
    name="shared_auth_core",
    sources=["**/*.py"],
    resolve="auth_core",
    dependencies=[
        "//3rdparty/python:auth_core_reqs#boto3",
        "//3rdparty/python:auth_core_reqs#redis",
        "//3rdparty/python:auth_core_reqs#pydantic",
        "//3rdparty/python:auth_core_reqs#pydantic-settings",
        "//3rdparty/python:auth_core_reqs#pyyaml",
    ],
)

# Shared library for web_core resolve
python_sources(
    name="shared_web_core",
    sources=["**/*.py"],
    resolve="web_core",
    dependencies=[
        "//3rdparty/python:web_core_reqs#boto3",
        "//3rdparty/python:web_core_reqs#redis",
        "//3rdparty/python:web_core_reqs#pydantic",
        "//3rdparty/python:web_core_reqs#pydantic-settings",
        "//3rdparty/python:web_core_reqs#pyyaml",
    ],
)

# Shared library for agent_core resolve
python_sources(
    name="shared_agent_core",
    sources=["**/*.py"],
    resolve="agent_core",
    dependencies=[
        "//3rdparty/python:agent_core_reqs#boto3",
        "//3rdparty/python:agent_core_reqs#redis",
        "//3rdparty/python:agent_core_reqs#pydantic",
        "//3rdparty/python:agent_core_reqs#pydantic-settings",
        "//3rdparty/python:agent_core_reqs#pyyaml",
    ],
)
