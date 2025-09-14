python_sources(
    name="web_core",
    sources=["domain/**/*.py", "adapters/**/*.py", "public/**/*.py"],
    # Reuse admin resolves initially
    resolve="web_core",
    dependencies=[
        "stack/libs/shared",
        "stack/events/libs",
        "3rdparty/python:web_core_reqs",
    ],
    overrides={
        "domain/**/*.py": {
            "dependencies": [
                "3rdparty/python:web_core_reqs#pydantic",
            ]
        },
    },
)

python_sources(
    name="web_api_src",
    sources=["app/api/**/*.py"],
    resolve="web_api",
    dependencies=[":web_core", "3rdparty/python:web_api_reqs"],
    overrides={
        "app/api/**/*.py": {
            "dependencies": [
                "3rdparty/python:web_api_reqs#fastapi",
                "3rdparty/python:web_api_reqs#uvicorn",
                "3rdparty/python:web_api_reqs#pydantic",
                "3rdparty/python:web_api_reqs#python-multipart",
            ]
        },
    },
)

python_sources(
    name="web_worker_src",
    sources=["app/worker/**/*.py"],
    resolve="web_core",
    dependencies=[":web_core"],
)

pex_binary(
    name="web_api_pex",
    entry_point="services.web.app.api.main:run",
    dependencies=[":web_api_src"],
)

pex_binary(
    name="web_worker_pex",
    entry_point="services.web.app.worker.run:main",
    dependencies=[":web_worker_src"],
)

docker_image(name="web_image", dependencies=[":web_api_pex"], image_tags=["latest"])
docker_image(name="web_worker_image", dependencies=[":web_worker_pex"], image_tags=["latest"])

python_tests(
    name="unit",
    sources=["tests/unit/**/*.py"],
    resolve="web_api",
    dependencies=[":web_core", ":web_api_src", ":web_worker_src"],
)
