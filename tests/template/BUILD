python_sources(
    sources=["*.py"],
    resolve="test",
)

python_tests(
    name="template_tests",
    sources=["test_*.py"],
    tags=["unit", "template"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#pytest",
        "//3rdparty/python:test_reqs#pytest-cookies",
        "//3rdparty/python:test_reqs#cookiecutter",
        "//3rdparty/python:test_reqs#cruft",
        "//3rdparty/python:test_reqs#pyyaml",
    ],
    run_goal_use_sandbox=False,
)

python_tests(
    name="test_cookiecutter_rendering",
    sources=["test_cookiecutter_rendering.py"],
    tags=["unit", "template", "cookiecutter"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#pytest",
        "//3rdparty/python:test_reqs#pytest-cookies",
        "//3rdparty/python:test_reqs#cookiecutter",
        "//3rdparty/python:test_reqs#cruft",
    ],
    run_goal_use_sandbox=False,
)

python_tests(
    name="test_template_validation",
    sources=["test_template_validation.py"],
    tags=["integration", "template", "validation"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#pytest",
        "//3rdparty/python:test_reqs#pyyaml",
    ],
    # Run in-repo to access project files
    run_goal_use_sandbox=False,
)
