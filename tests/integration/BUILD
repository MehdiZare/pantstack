python_sources(
    sources=["*.py"],
    resolve="test",
)

python_tests(
    name="test_localstack_services",
    sources=["test_localstack_services.py"],
    tags=["integration", "localstack", "slow"],
    timeout=300,
    resolve="test",
)

python_tests(
    name="test_supabase_integration",
    sources=["test_supabase_integration.py"],
    tags=["integration", "supabase", "slow"],
    timeout=300,
    resolve="test",
)

python_tests(
    name="test_docker_compose",
    sources=["test_docker_compose.py"],
    tags=["integration", "docker", "slow"],
    timeout=300,
    resolve="test",
)

python_tests(
    name="test_end_to_end",
    sources=["test_end_to_end.py"],
    tags=["integration", "e2e", "slow"],
    timeout=600,
    resolve="test",
)