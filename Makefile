.PHONY: help
help:
	@echo "Make targets for example"
	@echo "make init - Set up dev environment"
	@echo "make run - Start a local development instance"
	@echo "make update - Update pinned dependencies and run make init"
	@echo "make update-deps - Update pinned dependencies"
	@echo "make docker-build - Build the main Sasquatch application image"
	@echo "make docker-build-backup - Build the Sasquatch backup utility image"

.PHONY: init
init:
	uv sync --frozen --all-groups
	uv run pre-commit install

.PHONY: run
run:
	tox run -e run

.PHONY: update
update: update-deps init

.PHONY: update-deps
update-deps:
	uv lock --upgrade
	uv run --only-group=lint pre-commit autoupdate
	./scripts/update-uv-version.sh

.PHONY: docker-build
docker-build:
	docker build -t sasquatch:dev .

.PHONY: docker-build-backup
docker-build-backup:
	docker build -f backup/Dockerfile -t sasquatch-backup:dev .
