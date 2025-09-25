python_sources(
    name="auth_core",
    sources=["lib/**/*.py", "public/**/*.py"],
    resolve="auth_core",
    dependencies=["//stack/libs/shared:shared_auth_core", "3rdparty/python:auth_core_reqs"],
)

python_sources(
    name="auth_api_src",
    sources=["app/api/**/*.py"],
    resolve="auth_api",
    dependencies=["3rdparty/python:auth_api_reqs"],
    overrides={
        "app/api/**/*.py": {
            "dependencies": [
                "3rdparty/python:auth_api_reqs#fastapi",
                "3rdparty/python:auth_api_reqs#uvicorn",
                "3rdparty/python:auth_api_reqs#pydantic",
                "3rdparty/python:auth_api_reqs#dependency-injector",
            ]
        },
    },
)

pex_binary(
    name="auth_api_pex",
    entry_point="services.auth.app.api.main:run",
    resolve="auth_api",
    dependencies=[":auth_api_src"],
)

docker_image(
    name="auth_image",
    dependencies=[":auth_api_pex"],
    image_tags=["latest"],
    source="Dockerfile.api",
)

python_source(
    name="test_utils",
    source="tests/conftest.py",
    resolve="test",
    dependencies=[
        "//stack/libs/shared:shared_test",
        "3rdparty/python:test_reqs#pytest",
        "3rdparty/python:test_reqs#fastapi",
        "3rdparty/python:test_reqs#httpx",
    ],
)

python_tests(
    name="unit",
    sources=["tests/unit/**/*.py"],
    resolve="test",
    dependencies=[
        ":test_utils",
        "//stack/libs/shared:shared_test",
        "3rdparty/python:test_reqs#pytest",
        "3rdparty/python:test_reqs#fastapi",
        "3rdparty/python:test_reqs#httpx",
        "3rdparty/python:test_reqs#boto3",
    ],
)
