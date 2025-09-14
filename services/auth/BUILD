python_sources(
    name="auth_core",
    sources=["domain/**/*.py", "adapters/**/*.py", "public/**/*.py"],
    resolve="auth_core",
    dependencies=["stack/libs/shared", "3rdparty/python:auth_core_reqs"],
    overrides={
        "adapters/repositories/**/*.py": {
            "dependencies": [
                "3rdparty/python:auth_core_reqs#boto3",
            ]
        },
    },
)

python_sources(
    name="auth_api_src",
    sources=["app/api/**/*.py"],
    resolve="auth_api",
    dependencies=[":auth_core", "3rdparty/python:auth_api_reqs"],
    overrides={
        "app/api/**/*.py": {
            "dependencies": [
                "3rdparty/python:auth_api_reqs#fastapi",
                "3rdparty/python:auth_api_reqs#uvicorn",
                "3rdparty/python:auth_api_reqs#pydantic",
            ]
        },
    },
)

pex_binary(
    name="auth_api_pex",
    entry_point="services.auth.app.api.main:run",
    dependencies=[":auth_api_src"],
)

docker_image(
    name="auth_image",
    dependencies=[":auth_api_pex"],
    image_tags=["latest"],
    source="Dockerfile.api",
)

python_tests(
    name="unit",
    sources=["tests/unit/**/*.py"],
    resolve="auth_api",
    dependencies=[
        ":auth_core",
        ":auth_api_src",
        "3rdparty/python:auth_api_reqs#fastapi",
        "3rdparty/python:auth_api_reqs#httpx",
    ],
)
