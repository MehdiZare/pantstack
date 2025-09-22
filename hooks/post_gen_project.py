#!/usr/bin/env python3
"""Post-generation hook for Pantstack template.

This script runs automatically after cookiecutter/cruft generates a new project.
It cleans up template-specific files and prepares the project for immediate use.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command: list, cwd: str = ".") -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr."""
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def cleanup_template_files():
    """Remove template-specific files and directories."""
    print("\n🧹 Cleaning up template-specific files...")

    # Files and directories to remove
    items_to_remove = [
        # Directories
        ("cli", "CLI tests directory"),
        ("tests/template", "Template validation tests"),
        ("tests/scripts", "Script validation tests"),
        ("tests/cli", "CLI integration tests"),
        ("hooks", "Cookiecutter hooks"),
        # Scripts
        ("scripts/publish_template.sh", "Template publishing script"),
        ("scripts/create_project_from_template.sh", "Template creation script"),
        ("scripts/quickstart.sh", "Template quickstart wizard"),
        ("scripts/cleanup_template.sh", "Template cleanup script"),
        # GitHub workflows
        (".github/workflows/template-release.yml", "Template release workflow"),
        (".github/workflows/test-template.yml", "Template testing workflow"),
        # Documentation
        ("docs/TEMPLATE_USAGE.md", "Template usage guide"),
        ("TEMPLATE_README.md", "Template README"),
        # Cookiecutter files
        ("cookiecutter.json", "Cookiecutter configuration"),
        (".cruft.json", "Cruft configuration"),
    ]

    removed_count = 0
    for item_path, description in items_to_remove:
        path = Path(item_path)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"  ✓ Removed {description}")
            removed_count += 1

    # Clean up pants.toml
    pants_toml = Path("pants.toml")
    if pants_toml.exists():
        content = pants_toml.read_text()
        lines_to_remove = [
            'cli_test = "lockfiles/cli_test.lock"',
            'template_test = "lockfiles/template_test.lock"',
        ]

        modified = False
        for line in lines_to_remove:
            if line in content:
                content = content.replace(line + "\n", "")
                modified = True

        if modified:
            pants_toml.write_text(content)
            print("  ✓ Cleaned up pants.toml")

    # Clean up orphaned lockfiles
    lockfiles_to_remove = [
        "lockfiles/cli_test.lock",
        "lockfiles/template_test.lock",
    ]

    for lockfile in lockfiles_to_remove:
        path = Path(lockfile)
        if path.exists():
            path.unlink()
            print(f"  ✓ Removed {path.name}")

    # Clean up requirements
    requirements_to_remove = [
        "3rdparty/python/requirements-cli-test.txt",
        "3rdparty/python/requirements-template-test.txt",
    ]

    for req_file in requirements_to_remove:
        path = Path(req_file)
        if path.exists():
            path.unlink()
            print(f"  ✓ Removed {path.name}")

    print(f"\n✅ Removed {removed_count} template-specific items")
    return True


def check_and_install_tools():
    """Check if essential tools are installed and offer to install them."""
    print("\n🔧 Checking development tools...")

    # Check if setup-tools.sh exists
    setup_script = Path("scripts/setup-tools.sh")
    if not setup_script.exists():
        print("  ⚠️  setup-tools.sh not found, skipping tool installation")
        return

    # Run setup-tools.sh to check/install tools
    print("  Running setup-tools.sh to verify dependencies...")
    returncode, stdout, stderr = run_command(["bash", "scripts/setup-tools.sh"])

    if returncode == 0:
        print("  ✓ Development tools checked")
    else:
        print("  ⚠️  Tool setup had issues, please run 'make setup' manually")


def initialize_project():
    """Initialize the project with default configuration."""
    print("\n🚀 Initializing your new monorepo...")

    # Check if .env.example exists and create .env
    env_example = Path(".env.example")
    env_file = Path(".env")

    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("  ✓ Created .env from .env.example")
        print("  ⚠️  Remember to update .env with your actual values!")

    # Initialize git repository if not already initialized
    if not Path(".git").exists():
        print("  Initializing git repository...")
        run_command(["git", "init"])
        run_command(["git", "checkout", "-b", "main"])
        print("  ✓ Git repository initialized")

    # Install pre-commit hooks
    print("  Installing pre-commit hooks...")
    returncode, _, stderr = run_command(["pip", "install", "--quiet", "pre-commit"])
    if returncode == 0:
        returncode, _, stderr = run_command(["pre-commit", "install"])
        if returncode == 0:
            print("  ✓ Pre-commit hooks installed")
        else:
            print(f"  ⚠️  Failed to install pre-commit hooks: {stderr}")
    else:
        print("  ⚠️  Failed to install pre-commit package")
        print("     Run manually: pip install pre-commit && pre-commit install")

    # Create initial commit
    print("  Creating initial commit...")
    run_command(["git", "add", "-A"])
    run_command(["git", "commit", "-m", "Initial commit from Pantstack template"])
    print("  ✓ Initial commit created")


def print_next_steps():
    """Print helpful next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 Your Pantstack monorepo is ready!")
    print("=" * 60)
    print("\nNext steps:")
    print("\n1. Configure your environment:")
    print("   cd {{ cookiecutter.project_slug }}")
    print("   vim .env  # Add your AWS, GitHub, and Pulumi credentials")
    print("\n2. Install development tools:")
    print("   make setup  # Install Pants, Docker, AWS CLI, etc.")
    print("\n3. Bootstrap infrastructure:")
    print("   make bootstrap  # Set up GitHub repo, ECR, and CI/CD")
    print("\n4. Create your first service:")
    print("   make new-service S=api  # Creates a new microservice")
    print("\n5. Start local development:")
    print("   make up  # Start Docker services")
    print("   supabase start  # Start Supabase (if using)")
    print("\nFor more information:")
    print("  - README.md - Project overview")
    print("  - docs/CLI_COMMANDS.md - All available commands")
    print("  - CLAUDE.md - AI assistant guidance")
    print("\nHappy coding! 🚀")


def main():
    """Main entry point for post-generation hook."""
    print("\n🎨 Pantstack Template - Post-Generation Setup")
    print("=" * 60)

    try:
        # Step 1: Clean up template files
        cleanup_success = cleanup_template_files()
        if not cleanup_success:
            print("⚠️  Some cleanup tasks failed, but continuing...")

        # Step 2: Check and install tools (optional)
        # Commented out by default to avoid lengthy installation during generation
        # Uncomment if you want automatic tool installation
        # check_and_install_tools()

        # Step 3: Initialize project
        initialize_project()

        # Step 4: Print next steps
        print_next_steps()

        return 0

    except Exception as e:
        print(f"\n❌ Error during post-generation setup: {e}")
        print("\nYou can manually run cleanup with:")
        print("  bash scripts/cleanup_template.sh")
        return 1


if __name__ == "__main__":
    sys.exit(main())
