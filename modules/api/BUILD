python_sources(
    name="api_core",
    sources=["backend/{service,worker,schemas,public}/**/*.py"],
    resolve="api_core",
    dependencies=["platform/libs/shared", "3rdparty/python:api_core_reqs"],
)

python_sources(
    name="api_api_src",
    sources=["backend/api/**/*.py"],
    resolve="api_api",
    dependencies=[":api_core", "3rdparty/python:api_api_reqs"],
)

pex_binary(
    name="api_api_pex",
    entry_point="modules.api.backend.api.main:run",
    dependencies=[":api_api_src"],
)

pex_binary(
    name="api_worker_pex",
    entry_point="modules.api.backend.worker.run:main",
    dependencies=[":api_core"],
)

docker_image(
    name="api_image",
    dependencies=[":api_api_pex"],
    version_tags=["latest"],
)

docker_image(
    name="api_worker_image",
    dependencies=[":api_worker_pex"],
    version_tags=["latest"],
)

python_tests(name="unit", sources=["backend/tests/unit/**/*.py"], resolve="tests", dependencies=[":api_core"])

