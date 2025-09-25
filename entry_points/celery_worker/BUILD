python_sources(
    name="celery_sources",
    sources=["**/*.py"],
    resolve="celery_main",
    dependencies=[
        "//shared/core:core",
        "//shared/utils:utils",
        "//stack/agents:agents",
    ],
)

pex_binary(
    name="celery_worker",
    entry_point="run.py",
    dependencies=[
        ":celery_sources",
    ],
    resolve="celery_main",
)

docker_image(
    name="celery_worker_image",
    dependencies=[
        ":celery_worker",
    ],
    instructions=[
        "FROM python:3.11-slim",
        "COPY celery_worker.pex /app/",
        "WORKDIR /app",
        'ENTRYPOINT ["./celery_worker.pex"]',
    ],
)
