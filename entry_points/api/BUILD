python_sources(
    name="api_sources",
    sources=["**/*.py"],
    resolve="api_main",
    dependencies=[
        "//shared/core:core",
        "//shared/utils:utils",
    ],
)

pex_binary(
    name="api_main",
    entry_point="main.py",
    dependencies=[
        ":api_sources",
    ],
    resolve="api_main",
)

docker_image(
    name="api_image",
    dependencies=[
        ":api_main",
    ],
    instructions=[
        "FROM python:3.11-slim",
        "COPY api_main.pex /app/",
        "WORKDIR /app",
        'ENTRYPOINT ["./api_main.pex"]',
    ],
)
