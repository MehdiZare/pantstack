python_sources(
    name="agent_core",
    sources=["domain/**/*.py", "adapters/**/*.py", "public/**/*.py"],
    resolve="agent_core",
    dependencies=["stack/libs/shared", "stack/agents", "stack/events/libs", "3rdparty/python:agent_core_reqs"],
)

python_sources(
    name="agent_worker_src",
    sources=["app/worker/**/*.py"],
    resolve="agent_core",
    dependencies=[":agent_core"],
)

pex_binary(
    name="agent_worker_pex",
    entry_point="services.agent.app.worker.run:main",
    dependencies=[":agent_worker_src"],
)

docker_image(name="agent_worker_image", dependencies=[":agent_worker_pex"], image_tags=["latest"])

python_tests(name="unit", sources=["tests/unit/**/*.py"], resolve="agent_core", dependencies=[":agent_core", ":agent_worker_src"])
