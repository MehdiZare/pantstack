
.DEFAULT_GOAL := help

.PHONY: help quickstart new-project template-help init-template seed-labels template-setup docs-serve docs-build docs-publish \
	boot fmt lint test up down dev-up dev-down package mod mod-s locks pre-commit-install bootstrap \
	new-module stack-init stack-up stack-destroy stack-preview stack-outputs \
	stack-verify verify-dev verify-prod seed-stacks esc-init esc-attach publish-template create-project gha-ci gha-deploy gh-new-branch gh-open-pr \
	gh-new-module-pr

help: ## Show this help message
	@echo "Pantstack Monorepo Commands:"
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
	@grep -E '^(boot|fmt|lint|test|package|up|down|dev-up|dev-down|mod-s|locks|pre-commit-install|dev-api-s|dev-worker-s|svc-stack-init|svc-stack-up|svc-stack-destroy|svc-stack-preview|svc-stack-outputs|svc-verify-dev|svc-verify-prod):.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@printf "\033[33m━━━ Infrastructure Commands ━━━\033[0m\n"
	@grep -E '^(bootstrap|seed-stacks|svc-stack-|esc-|svc-verify-):.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@printf "\033[33m━━━ GitHub/CI Commands ━━━\033[0m\n"
	@grep -E '^(gha-|gh-):.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
    @echo "Examples:"
    @echo "  make quickstart       # Interactive setup wizard"
    @echo "  make new-project      # Create project from template"
    @echo "  make mod-s S=web      # Test and package a service"
    @echo "  make svc-stack-up S=web ENV=test  # Deploy a service"

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
	./pants lint :: && ./pants typecheck ::

test:   ## Run all tests
	./pants test ::

package: ## Build Docker images
	./pants package services/**:*image

up:     ## Start local stack
	docker compose up -d --build

down:   ## Stop local stack
	docker compose down -v

dev-up: ## Start LocalStack for local development
	docker compose -f docker-compose.local.yml up -d localstack redis

dev-down: ## Stop LocalStack for local development
	docker compose -f docker-compose.local.yml down -v

dev-api-s: ## Run service API locally (e.g., make dev-api-s S=web)
	python -c "from services.$(S).app.api.main import run; run()"

dev-worker-s: ## Run service worker locally (e.g., make dev-worker-s S=agent)
	python -c "from services.$(S).app.worker.run import main; main()"


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

gh-new-module-pr: ## Create module PR (e.g., make gh-new-module-pr M=orders)
	@b=$${B:-feature/add-$(M)-module}; \
	git checkout -b $$b; \
	M=$(M) ./scripts/new_module.sh; \
	git add -A; \
	git commit -m "feat($(M)): scaffold module"; \
	git push -u origin $$b; \
	gh pr create --base dev --head $$b --title "feat($(M)): scaffold module" --body "Scaffold $(M) module via template script."

verify-dev: ## Verify test environment (e.g., make verify-dev MS="api orders")
	@chmod +x scripts/verify_http.sh; \
	for m in $${MS:-$$(ls modules)}; do \
	  base=$$(pulumi -C modules/$$m/infrastructure stack output alb_dns --stack $(PULUMI_ORG)/$$m/test 2>/dev/null || true); \
	  if [ -n "$$base" ]; then \
	    echo "Verifying $$m (test) at http://$$base"; \
	    ./scripts/verify_http.sh http://$$base || exit 1; \
	  else \
	    echo "Skip $$m: no alb_dns output for test"; \
	  fi; \
	done

verify-prod: ## Verify production environment (e.g., make verify-prod MS="api")
	@chmod +x scripts/verify_http.sh; \
	for m in $${MS:-$$(ls modules)}; do \
	  base=$$(pulumi -C modules/$$m/infrastructure stack output alb_dns --stack $(PULUMI_ORG)/$$m/prod 2>/dev/null || true); \
	  if [ -n "$$base" ]; then \
	    echo "Verifying $$m (prod) at http://$$base"; \
	    ./scripts/verify_http.sh http://$$base || exit 1; \
	  else \
	    echo "Skip $$m: no alb_dns output for prod"; \
	  fi; \
	done
