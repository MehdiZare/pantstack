python_sources(
    name="auth_core",
    sources=["backend/{service,repo,schemas,public}/**/*.py"],
    resolve="auth_core",
    dependencies=["platform/libs/shared"],
)

python_sources(
    name="auth_api_src",
    sources=["backend/api/**/*.py"],
    resolve="auth_api",
    dependencies=[":auth_core", "3rdparty/python:auth_api_reqs"],
)

pex_binary(
    name="auth_api_pex",
    entry_point="modules.auth.backend.api.main:run",
    dependencies=[":auth_api_src"],
)

docker_image(
    name="auth_image",
    dependencies=[":auth_api_pex"],
    version_tags=["latest"],
)

python_tests(name="unit",        sources=["backend/tests/unit/**/*.py"],        resolve="tests", dependencies=[":auth_core"])
python_tests(name="integration", sources=["backend/tests/integration/**/*.py"], resolve="tests", dependencies=[":auth_api_src"])
python_tests(name="e2e",         sources=["backend/tests/e2e/**/*.py"],         resolve="tests", dependencies=[":auth_api_src"])
