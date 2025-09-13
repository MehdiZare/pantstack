python_sources(
    name="admin_core",
    sources=["backend/{service,schemas,public}/**/*.py"],
    resolve="admin_core",
    dependencies=["platform/libs/shared", "3rdparty/python:admin_core_reqs", "platform/agents"],
)

python_sources(
    name="admin_api_src",
    sources=["backend/api/**/*.py"],
    resolve="admin_api",
    dependencies=[":admin_core", "3rdparty/python:admin_api_reqs"],
)

pex_binary(
    name="admin_api_pex",
    entry_point="modules.admin.backend.api.main:run",
    dependencies=[":admin_api_src"],
)

python_sources(
    name="admin_worker_src",
    sources=["backend/worker/**/*.py"],
    resolve="admin_core",
    dependencies=[":admin_core"],
)

pex_binary(
    name="admin_worker_pex",
    entry_point="modules.admin.backend.worker.run:main",
    dependencies=[":admin_worker_src"],
)

pex_binary(
    name="admin_celery_worker_pex",
    entry_point="modules.admin.backend.worker.celery_run:main",
    dependencies=[":admin_worker_src"],
)

pex_binary(
    name="admin_scheduler_pex",
    entry_point="modules.admin.backend.scheduler.loop:main",
    dependencies=[":admin_core"],
)

docker_image(name="admin_image", dependencies=[":admin_api_pex"], image_tags=["latest"])
docker_image(name="admin_worker_image", dependencies=[":admin_worker_pex"], image_tags=["latest"])
docker_image(name="admin_celery_worker_image", dependencies=[":admin_celery_worker_pex"], image_tags=["latest"])

python_tests(name="unit", sources=["backend/tests/unit/**/*.py"], resolve="tests", dependencies=[":admin_core", ":admin_api_src", ":admin_worker_src"])
