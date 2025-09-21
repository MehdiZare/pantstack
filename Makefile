
.DEFAULT_GOAL := help

.PHONY: help quickstart new-project template-help init-template seed-labels template-setup docs-serve docs-build docs-publish \
	boot fmt lint test up down dev-up dev-down package mod mod-s locks pre-commit-install bootstrap \
	stack-init stack-up stack-destroy stack-preview stack-outputs \
	stack-verify verify-dev verify-prod seed-stacks esc-init esc-attach publish-template create-project gha-ci gha-deploy gh-new-branch gh-open-pr \
	gh-new-service-pr test-service-lifecycle test-service-integration test-create-cleanup clean-test-services \
	cleanup-template init-project

help: ## Show this help message
	@echo "Pantstack Monorepo Commands:"
	@echo ""
	@printf "\033[33m━━━ Setup Commands ━━━\033[0m\n"
	@printf "  \033[36m%-20s\033[0m %s\n" "setup" "Complete development environment setup"
	@printf "  \033[36m%-20s\033[0m %s\n" "setup-quick" "Quick setup (no prompts)"
	@printf "  \033[36m%-20s\033[0m %s\n" "check-tools" "Verify all tools are installed"
	@echo ""
	@printf "\033[33m━━━ Template Commands ━━━\033[0m\n"
	@printf "  \033[36m%-20s\033[0m %s\n" "quickstart" "Interactive setup wizard"
	@printf "  \033[36m%-20s\033[0m %s\n" "new-project" "Create new project from this template"
	@printf "  \033[36m%-20s\033[0m %s\n" "init-template" "Initialize as reusable template"
	@printf "  \033[36m%-20s\033[0m %s\n" "template-help" "Show template usage guide"
	@printf "  \033[36m%-20s\033[0m %s\n" "publish-template" "Publish repo as GitHub template"
	@printf "  \033[36m%-20s\033[0m %s\n" "create-project" "Create new project from template"
	@echo ""
	@printf "\033[33m━━━ Development Commands ━━━\033[0m\n"
	@grep -E '^(boot|fmt|lint|test|test-unit|test-integration|test-setup|test-shared|test-coverage|package|up|down|dev-up|dev-down|mod-s|locks|pre-commit-install|dev-api-s|dev-worker-s|svc-stack-init|svc-stack-up|svc-stack-destroy|svc-stack-preview|svc-stack-outputs|svc-verify-dev|svc-verify-prod):.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@printf "\033[33m━━━ Infrastructure Commands ━━━\033[0m\n"
	@grep -E '^(bootstrap|seed-stacks|svc-stack-|esc-|svc-verify-):.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@printf "\033[33m━━━ GitHub/CI Commands ━━━\033[0m\n"
	@grep -E '^(gha-|gh-):.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make setup            # Install all required tools"
	@echo "  make quickstart       # Interactive setup wizard"
	@echo "  make new-project      # Create project from template"
	@echo "  make mod-s S=web      # Test and package a service"
	@echo "  make svc-stack-up S=web ENV=test  # Deploy a service"

# Development Environment Setup
setup: ## Complete development environment setup with prompts
	@./scripts/setup-tools.sh

setup-quick: ## Quick setup without prompts (macOS/Linux)
	@./scripts/quick-setup.sh

check-tools: ## Verify all required tools are installed
	@./scripts/setup/verify-tools.sh

cleanup-template: ## Remove template-specific files (for end users)
	@echo "🧹 Cleaning up template-specific files..."
	@if [ -f scripts/cleanup_template.sh ]; then \
		bash scripts/cleanup_template.sh; \
	else \
		echo "Cleanup script not found (may have already been removed)"; \
	fi

init-project: ## Initialize project after template creation (cleanup + setup)
	@echo "🚀 Initializing your new monorepo project..."
	@if [ -f scripts/cleanup_template.sh ]; then \
		bash scripts/cleanup_template.sh; \
	fi
	@echo ""
	@echo "📦 Setting up development environment..."
	@./scripts/setup-tools.sh
	@echo ""
	@echo "✅ Project initialization complete!"
	@echo "Next: Configure .env file and run 'make bootstrap'"

quickstart: ## Interactive setup wizard (template or project)
	@./scripts/quickstart.sh

new-project: ## Create new project from this template interactively
	@echo "Starting interactive project creation..."
	@if ! command -v cruft >/dev/null 2>&1; then \
		echo "Installing cruft..."; \
		pip install --user cruft || pipx install cruft; \
	fi
	@cruft create .

template-help: ## Show how to use this template
	@printf "\033[36m━━━ Pantstack Template Usage Guide ━━━\033[0m\n"
	@echo ""
	@echo "This repository can be used as a template in two ways:"
	@echo ""
	@printf "\033[33m1. As a Cookiecutter Template (Recommended)\033[0m\n"
	@echo "   Advantages: Interactive prompts, template updates, variable substitution"
	@echo "   Usage:"
	@echo "     Local:  make new-project"
	@echo "     Remote: cruft create gh:owner/repo"
	@echo ""
	@printf "\033[33m2. As a GitHub Template\033[0m\n"
	@echo "   Advantages: Simple, no tools needed, GitHub UI"
	@echo "   Usage:"
	@echo "     1. Publish: make init-template"
	@echo "     2. Click 'Use this template' on GitHub"
	@echo ""
	@printf "\033[33mFor Template Authors:\033[0m\n"
	@echo "   make init-template    # Set up and publish your template"
	@echo "   make publish-template # Republish after changes"
	@echo ""
	@printf "\033[33mFor Template Users:\033[0m\n"
	@echo "   make quickstart      # Interactive wizard"
	@echo "   make new-project     # Create from local template"

init-template: ## Initialize and publish as reusable template
	@echo "Initializing template repository..."
	@if [ ! -f .env ] && [ -f .env.example ]; then \
		cp .env.example .env; \
		echo "Created .env - please edit it with your values"; \
		echo "Then run 'make init-template' again"; \
		exit 1; \
	fi
	@./scripts/publish_template.sh
	@echo ""
	@printf "\033[32m✅ Template ready! Others can now use:\033[0m\n"
	@echo "  cruft create gh:$${GITHUB_OWNER}/$${GITHUB_REPO}"

seed-labels: ## Create GitHub release labels for versioning
	@./scripts/seed_labels.sh

template-setup: ## Complete template setup (init + labels + docs)
	@echo "Setting up template repository..."
	@$(MAKE) init-template
	@echo ""
	@echo "Installing pre-commit hooks..."
	@$(MAKE) pre-commit-install
	@echo ""
	@echo "Creating release labels..."
	@$(MAKE) seed-labels
	@echo ""
	@printf "\033[32m✅ Template setup complete!\033[0m\n"
	@echo "Next steps:"
	@echo "1. Run 'pre-commit run --all-files' to check formatting"
	@echo "2. Push changes to dev branch"
	@echo "3. Create PR from dev to main with version label"
	@echo "4. Documentation will be published to GitHub Pages"

docs-serve: ## Serve documentation locally
	@./scripts/docs_serve.sh

docs-build: ## Build documentation
	@echo "Building documentation..."
	@pip install -q mkdocs mkdocs-material mkdocs-mermaid2-plugin pymdown-extensions 2>/dev/null || true
	@mkdocs build --clean

docs-publish: ## Manually publish docs to GitHub Pages
	@echo "Publishing documentation to GitHub Pages..."
	@gh workflow run docs-publish.yml

boot:   ## Install Pants build system
	curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
	@echo "Run: export PATH=\"\$$HOME/.local/bin:\$$PATH\" to add pants to your PATH"
	@echo "You can also use the repo-local './pants' wrapper in all commands."

fmt:    ## Format code
	./pants fmt ::

lint:   ## Lint and typecheck
	./pants lint :: && ./pants check ::

test:   ## Run all tests
	./pants test ::

test-unit: ## Run unit tests only
	./pants test :: --tag=unit

test-integration: ## Run integration tests (requires dev-up)
	ENV=test LOCALSTACK=true ./pants test :: --tag=integration

test-setup: ## Run setup and CLI tests
	./pants test scripts/tests:: cli/tests::

test-shared: ## Run shared library tests
	./pants test shared/tests::

test-service: ## Test specific service (S=service_name)
	./pants test services/$(S)::

test-coverage: ## Generate coverage report for all tests
	./pants test :: --test-use-coverage

test-coverage-report: ## Generate HTML coverage report
	./pants test :: --test-use-coverage
	@echo "Coverage report generated by Pants"

test-fast: ## Run fast tests only (exclude slow integration tests)
	./pants test :: --tag=-slow

test-slow: ## Run slow tests only (integration, e2e)
	./pants test :: --tag=slow

test-watch: ## Run tests in watch mode
	./pants test :: --loop

package: ## Build Docker images
	./pants package "services/**:*image"

# LocalStack & Development Commands
localstack-up: ## Start LocalStack with initialization
	@echo "🚀 Starting LocalStack..."
	docker compose up -d localstack
	@echo "⏳ Waiting for LocalStack to be ready..."
	@sleep 5
	@docker compose logs localstack | tail -20
	@echo "✅ LocalStack is ready at http://localhost:4566"

localstack-init: ## Initialize LocalStack resources
	@echo "🔧 Initializing LocalStack resources..."
	@docker exec $$(docker ps -q -f name=localstack) sh -c "cd /etc/localstack/init/ready.d && sh 01-create-resources.sh && sh 02-seed-data.sh"

localstack-reset: ## Reset LocalStack to clean state
	docker compose down -v localstack
	docker compose up -d localstack
	@sleep 5
	$(MAKE) localstack-init

localstack-logs: ## Show LocalStack logs
	docker compose logs -f localstack

up:     ## Start full local stack with LocalStack
	LOCALSTACK=true docker compose up -d --build
	@echo "⏳ Waiting for services..."
	@sleep 10
	@echo "✅ Services ready:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Flower: http://localhost:5555"
	@echo "  - LocalStack: http://localhost:4566"

down:   ## Stop local stack
	docker compose down -v

dev-up: ## Start minimal dev stack (Redis, LocalStack) - run 'supabase start' separately for DB
	docker compose up -d redis localstack
	@sleep 5
	@echo "✅ Dev services ready (remember to run 'supabase start' for database)"

dev-down: ## Stop dev services
	docker compose down redis localstack

# Configuration Management
config-init: ## Initialize configuration files from templates
	@echo "📝 Initializing configuration..."
	@cp -n .env.example .env 2>/dev/null || echo ".env already exists"
	@cp -n config/environments/development.yaml config/local.yaml 2>/dev/null || echo "local config exists"
	@echo "✅ Configuration initialized"

config-validate: ## Validate current configuration
	@echo "🔍 Validating configuration..."
	@ENVIRONMENT=$${ENVIRONMENT:-development} python -c "from shared.core.config_strategy import ConfigLoader; from shared.core.health import ConfigValidator; from shared.core.config import BaseConfig; c = ConfigLoader.load(BaseConfig, 'test'); ConfigValidator.assert_valid(c); print('✅ Configuration is valid')"

config-show: ## Show resolved configuration
	@echo "📋 Current configuration:"
	@ENVIRONMENT=$${ENVIRONMENT:-development} python -c "from shared.core.config_strategy import ConfigLoader; from shared.core.config import BaseConfig; c = ConfigLoader.load(BaseConfig, 'test'); print(c.mask_secrets())"

# Development Helpers
dev-api: ## Run API locally with LocalStack
	LOCALSTACK=true ENVIRONMENT=development python -m entry_points.api.run

dev-worker: ## Run Celery worker locally with LocalStack
	LOCALSTACK=true ENVIRONMENT=development celery -A entry_points.celery_worker.app worker --loglevel=info

dev-shell: ## Start Python shell with initialized environment
	LOCALSTACK=true ENVIRONMENT=development python -c "from shared.core.config_strategy import ConfigLoader; from shared.core.config import BaseConfig; from shared.core.aws_factory import get_aws_factory; config = ConfigLoader.load(BaseConfig, 'dev'); aws = get_aws_factory(); import IPython; IPython.embed(header='Pantstack Dev Shell\\nConfig: config\\nAWS: aws')"

dev-test: ## Run tests with LocalStack
	ENV=test LOCALSTACK=true ./pants test :: --tag=integration

# AWS/LocalStack Commands
aws-ls: ## Run AWS CLI against LocalStack
	aws --endpoint-url=http://localhost:4566 $(CMD)

ls-tables: ## List DynamoDB tables in LocalStack
	@aws --endpoint-url=http://localhost:4566 dynamodb list-tables --output table

ls-queues: ## List SQS queues in LocalStack
	@aws --endpoint-url=http://localhost:4566 sqs list-queues --output table

ls-buckets: ## List S3 buckets in LocalStack
	@aws --endpoint-url=http://localhost:4566 s3 ls

ls-params: ## List SSM parameters in LocalStack
	@aws --endpoint-url=http://localhost:4566 ssm describe-parameters --output table


dev-stop: ## Stop background dev processes
	@if [ -f .dev/pids ]; then \
	  xargs kill -9 < .dev/pids 2>/dev/null || true; \
	  rm -f .dev/pids; \
	  echo "Stopped background dev processes"; \
	else \
	  echo "No .dev/pids found"; \
	fi

mod-s:  ## Test and package a service (e.g., make mod-s S=web)
	./pants test services/$(S)/:: && ./pants package services/$(S):*image

locks:  ## Generate Pants lockfiles
	./pants generate-lockfiles

pre-commit-install: ## Install pre-commit hooks
	pip install pre-commit && pre-commit install

bootstrap: ## Bootstrap foundation infrastructure (requires .env)
	@echo "Installing pre-commit hooks..."
	@$(MAKE) pre-commit-install
	./scripts/bootstrap_foundation.sh

seed-stacks: ## Initialize Pulumi stacks for all services
	@for dir in services/*/infra/pulumi; do \
	  [ -d "$$dir" ] || continue; \
	  svc=$$(basename $$(dirname $$(dirname "$$dir"))); \
	  echo "-- $$svc (test)"; \
	  pulumi -C "$$dir" stack select "$(PULUMI_ORG)/$$svc/test" >/dev/null 2>&1 || pulumi -C "$$dir" stack init "$(PULUMI_ORG)/$$svc/test"; \
	  echo "-- $$svc (prod)"; \
	  pulumi -C "$$dir" stack select "$(PULUMI_ORG)/$$svc/prod" >/dev/null 2>&1 || pulumi -C "$$dir" stack init "$(PULUMI_ORG)/$$svc/prod"; \
	done

esc-init: ## Initialize Pulumi ESC environment (optional)
	./scripts/esc_init.sh

esc-attach: ## Attach ESC env to stack (e.g., make esc-attach M=api ENV=test)
	ESC_ENV_NAME=${ESC_ENV_NAME} M=$(M) ENV=$(ENV) ./scripts/esc_attach.sh

publish-template: ## Publish repo as GitHub template
	./scripts/publish_template.sh

create-project: ## Create new project from template
	TEMPLATE_REPO=${TEMPLATE_REPO} GITHUB_OWNER=${GITHUB_OWNER} ./scripts/create_project_from_template.sh

new-service: ## Scaffold new layered service (e.g., make new-service S=search)
	S=$(S) ./scripts/new_service.sh && ./pants generate-lockfiles

svc-stack-up: ## Deploy service stack (e.g., make svc-stack-up S=web ENV=test)
	cd services/$(S)/infra/pulumi && pulumi stack select $(PULUMI_ORG)/$(S)/$(ENV) || pulumi stack init $(PULUMI_ORG)/$(S)/$(ENV) && pulumi up -y

svc-stack-outputs: ## Show service stack outputs (e.g., make svc-stack-outputs S=web ENV=test)
	cd services/$(S)/infra/pulumi && pulumi stack output --json

gha-ci: ## Trigger CI workflow (requires gh CLI)
	gh workflow run ci.yml -r dev

gha-deploy: ## Trigger deploy workflow (e.g., make gha-deploy M=api ENV=prod)
	gh workflow run deploy.yml -f module=$(M) -f env=$(ENV)

gh-new-branch: ## Create new git branch (e.g., make gh-new-branch B=feature/x)
	git checkout -b $(B)

gh-open-pr: ## Open PR (e.g., make gh-open-pr B=feature/x BASE=dev TITLE="...")
	gh pr create --base $(BASE) --head $(B) --title "$(TITLE)" --body "$(BODY)"

gh-new-service-pr: ## Create service PR (e.g., make gh-new-service-pr S=orders)
	@b=$${B:-feature/add-$(S)-service}; \
	git checkout -b $$b; \
	S=$(S) ./scripts/new_service.sh; \
	git add -A; \
	git commit -m "feat($(S)): scaffold service"; \
	git push -u origin $$b; \
	gh pr create --base dev --head $$b --title "feat($(S)): scaffold service" --body "Scaffold $(S) service via template script."

# Service Lifecycle Testing
test-service-lifecycle: ## Run service lifecycle tests with cleanup
	@echo "🧪 Testing service lifecycle..."
	@./scripts/test/test_service_lifecycle.sh

test-service-integration: ## Run Python integration tests for services
	@echo "🐍 Running service integration tests..."
	@./pants test tests/integration/test_service_lifecycle.py --test-output=all || \
		python -m pytest tests/integration/test_service_lifecycle.py -v

test-create-cleanup: ## Test service creation and immediate cleanup
	@echo "🔄 Testing create/cleanup cycle..."
	@TEST_SVC="test_$$$$_$$(date +%s)"; \
	S=$$TEST_SVC ./scripts/new_service.sh && \
	echo "✅ Created service: $$TEST_SVC" && \
	ls -la services/$$TEST_SVC/BUILD && \
	echo "🧹 Cleaning up..." && \
	rm -rf services/$$TEST_SVC && \
	echo "✨ Cleanup complete"

clean-test-services: ## Clean any leftover test services
	@echo "🧹 Cleaning test services..."
	@find services -type d -name "test_*" -exec rm -rf {} + 2>/dev/null || true
	@find services -type d -name "temp_*" -exec rm -rf {} + 2>/dev/null || true
	@find services -type d -name "tmp_test_*" -exec rm -rf {} + 2>/dev/null || true
	@if [ -f ./pants ]; then ./pants --no-watch-filesystem gc 2>/dev/null || true; fi
	@echo "✨ Test services cleaned"

# Safe CLI Testing Commands
test-cli-safe: ## Run CLI tests with automatic cleanup
	@echo "🧪 Running CLI tests with cleanup..."
	@pytest tests/cli -m "not destructive" --tb=short || true
	@make clean-test-artifacts
	@echo "✅ CLI tests complete with cleanup"

test-cli-verify: ## Run tests and verify cleanup
	@echo "🔍 Checking for test artifacts before..."
	@python -c "from tests.cli.cleanup import TestCleanupManager; from pathlib import Path; m = TestCleanupManager(Path('.')); r = m.verify_cleanup(); print('  No artifacts found') if not r else print(f'  Found: {r}')"
	@echo "🧪 Running CLI tests..."
	@pytest tests/cli --tb=short || true
	@echo "✅ Verifying cleanup..."
	@python -c "from tests.cli.cleanup import TestCleanupManager; from pathlib import Path; m = TestCleanupManager(Path('.')); r = m.verify_cleanup(); exit(1) if r else print('  ✨ All clean!')"

clean-test-artifacts: ## Clean all test artifacts (services, containers, stacks)
	@echo "🧹 Cleaning all test artifacts..."
	@python -c "from tests.cli.cleanup import TestCleanupManager; from pathlib import Path; m = TestCleanupManager(Path('.')); results = m.clean_all(); print(f'  Cleaned: {sum(results.values())} items')"

clean-all-test-artifacts: ## Emergency cleanup of all test artifacts
	@echo "🚨 Emergency cleanup - removing all test artifacts..."
	@find services -type d -name "test_*" -exec rm -rf {} + 2>/dev/null || true
	@find services -type d -name "temp_*" -exec rm -rf {} + 2>/dev/null || true
	@find services -type d -name "tmp_test_*" -exec rm -rf {} + 2>/dev/null || true
	@docker ps -a --filter "name=test_" -q | xargs docker rm -f 2>/dev/null || true
	@docker ps -a --filter "name=temp_" -q | xargs docker rm -f 2>/dev/null || true
	@pulumi stack ls --json 2>/dev/null | jq -r '.[] | select(.name | contains("test-")) | .name' | xargs -I {} pulumi stack rm {} --force --yes 2>/dev/null || true
	@if [ -f ./pants ]; then ./pants --no-watch-filesystem gc 2>/dev/null || true; fi
	@echo "✨ Emergency cleanup complete"

check-test-artifacts: ## Check for any test artifacts
	@echo "🔍 Checking for test artifacts..."
	@python -c "from tests.cli.cleanup import TestCleanupManager; from pathlib import Path; m = TestCleanupManager(Path('.')); r = m.verify_cleanup(); print('  ✅ No artifacts found') if not r else (print(f'  ⚠️  Found artifacts: {r}'), exit(1))"

# CLI testing commands using appropriate execution modes
test-cli-integration: ## Run CLI integration tests with filesystem access
	@echo "🔧 Running integration tests with filesystem access..."
	@./pants run tests/cli:integration_test_runner
	@make verify-cleanup

test-cli-unit: ## Run CLI unit tests in sandbox
	@echo "📦 Running unit tests in sandbox..."
	@./pants test cli/tests:: --tag=unit

test-cli-all: ## Run all CLI tests (unit in sandbox, integration with filesystem access)
	@echo "📦 Running unit tests in sandbox..."
	@./pants test cli/tests:: --tag=unit
	@echo "🔧 Running integration tests with filesystem access..."
	@./pants run tests/cli:integration_test_runner
	@make verify-cleanup

verify-cleanup: ## Verify test cleanup
	@echo "🧹 Verifying cleanup..."
	@python -c "from tests.cli.cleanup import TestCleanupManager; from pathlib import Path; m = TestCleanupManager(Path('.')); r = m.verify_cleanup(); print('  ✅ Clean!') if not r else print(f'  ⚠️  Found: {r}')"

verify-dev: ## Verify test environment (e.g., make verify-dev MS="api orders")
	@chmod +x scripts/verify_http.sh; \
	for m in $${MS:-$$(ls services)}; do \
	  base=$$(pulumi -C services/$$m/infrastructure stack output alb_dns --stack $(PULUMI_ORG)/$$m/test 2>/dev/null || true); \
	  if [ -n "$$base" ]; then \
	    echo "Verifying $$m (test) at http://$$base"; \
	    ./scripts/verify_http.sh http://$$base || exit 1; \
	  else \
	    echo "Skip $$m: no alb_dns output for test"; \
	  fi; \
	done

verify-prod: ## Verify production environment (e.g., make verify-prod MS="api")
	@chmod +x scripts/verify_http.sh; \
	for m in $${MS:-$$(ls services)}; do \
	  base=$$(pulumi -C services/$$m/infrastructure stack output alb_dns --stack $(PULUMI_ORG)/$$m/prod 2>/dev/null || true); \
	  if [ -n "$$base" ]; then \
	    echo "Verifying $$m (prod) at http://$$base"; \
	    ./scripts/verify_http.sh http://$$base || exit 1; \
	  else \
	    echo "Skip $$m: no alb_dns output for prod"; \
	  fi; \
	done
