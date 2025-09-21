# Contributing to Pantstack

First off, thank you for considering contributing to Pantstack! It's people like you that make Pantstack such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets.
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include screenshots and animated GIFs** if possible.
* **Include your environment details** (OS, Python version, Pants version, etc.).

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Provide specific examples to demonstrate the steps**.
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
* **Include screenshots and animated GIFs** which help demonstrate the steps or the enhancement.
* **Explain why this enhancement would be useful** to most Pantstack users.

### Pull Requests

* Fork the repo and create your branch from `dev`.
* If you've added code that should be tested, add tests.
* If you've changed APIs, update the documentation.
* Ensure the test suite passes.
* Make sure your code follows the existing code style.
* Write a convincing description of your PR and why we should land it.

## Development Process

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/pantstack.git
   cd pantstack
   ```

2. **Set Up Development Environment**
   ```bash
   cp .env.example .env
   # Fill in your actual values
   make setup
   make boot
   ```

3. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Your Changes**
   * Write your code
   * Add/update tests
   * Update documentation

5. **Test Your Changes**
   ```bash
   make fmt      # Format code
   make lint     # Run linters
   make test     # Run tests
   ```

6. **Commit Your Changes**
   * Use [Conventional Commits](https://www.conventionalcommits.org/) format:
     * `feat:` for new features
     * `fix:` for bug fixes
     * `docs:` for documentation changes
     * `test:` for test changes
     * `refactor:` for refactoring
     * `chore:` for maintenance tasks

7. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   * Open a PR against the `dev` branch
   * Fill in the PR template
   * Link any related issues

## Project Structure

* `services/` - Individual microservices
* `stack/` - Shared libraries and infrastructure
* `docs/` - Documentation
* `.github/workflows/` - CI/CD workflows
* `scripts/` - Utility scripts
* `tests/` - Integration tests

## Style Guides

### Python Style Guide

* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
* Use [Black](https://black.readthedocs.io/) for formatting
* Use [isort](https://pycqa.github.io/isort/) for import sorting
* Use type hints where appropriate
* Write docstrings for all public functions

### Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Documentation Style

* Use Markdown for all documentation
* Include code examples where appropriate
* Keep language clear and concise
* Update README.md if you change functionality

## Testing

* Write unit tests for new functionality
* Ensure all tests pass before submitting PR
* Aim for good test coverage
* Use pytest for Python tests

## Additional Notes

### Issue and Pull Request Labels

* `bug` - Something isn't working
* `enhancement` - New feature or request
* `documentation` - Improvements or additions to documentation
* `good first issue` - Good for newcomers
* `help wanted` - Extra attention is needed
* `question` - Further information is requested

## Recognition

Contributors will be recognized in the project's README and release notes. We value all contributions, whether they're code, documentation, bug reports, or feature suggestions.

## Questions?

Feel free to open an issue with the `question` label or reach out to the maintainers directly.

Thank you for contributing to Pantstack!