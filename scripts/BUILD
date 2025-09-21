shell_sources(
    name="shell_scripts",
    sources=["*.sh", "setup/*.sh"],
)

# Specific file target for new_service.sh for test dependencies
files(
    name="new_service_script",
    sources=["new_service.sh"],
)

python_sources(
    name="tools",
    sources=["**/*.py"],
    resolve="test",  # Use test resolve for scripts
)