python_sources(
    name="event_processor_sources",
    sources=["**/*.py"],
    resolve="api_main",  # Using api_main resolve for now as event processor doesn't have its own
    dependencies=[
        "//shared/core:core",
        "//shared/utils:utils",
        "//stack/events:events",
    ],
)

pex_binary(
    name="event_processor",
    entry_point="main.py",
    dependencies=[
        ":event_processor_sources",
    ],
    resolve="api_main",
)

docker_image(
    name="event_processor_image",
    dependencies=[
        ":event_processor",
    ],
    instructions=[
        "FROM python:3.11-slim",
        "COPY event_processor.pex /app/",
        "WORKDIR /app",
        'ENTRYPOINT ["./event_processor.pex"]',
    ],
)