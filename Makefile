# Control Plane API - Docker Commands

.PHONY: help build up down logs shell migrate test clean

help: ## Show this help message
	@echo "Control Plane API - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@sed -n 's/^\.PHONY: //p' Makefile | sed 's/ .*//' | sed 's/^/  /' | sort

build: ## Build Docker images
	docker-compose build

up: ## Start all services (postgres + zitadel + api)
	docker-compose up

up-detach: ## Start all services in detached mode
	docker-compose up -d

down: ## Stop all services
	docker-compose down

down-volumes: ## Stop all services and remove volumes
	docker-compose down -v

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show logs from API service
	docker-compose logs -f api

logs-db: ## Show logs from database service
	docker-compose logs -f postgres

logs-zitadel: ## Show logs from Zitadel service
	docker-compose logs -f zitadel

shell: ## Open shell in API container
	docker-compose exec api sh

shell-db: ## Open psql shell in database container
	docker-compose exec postgres psql -U control_plane -d control_plane

migrate: ## Run database migrations
	docker-compose --profile migrate up migrate

test: ## Run tests in Docker container
	docker-compose exec api pytest -v

rebuild: ## Rebuild and restart services
	docker-compose up -d --build

clean: ## Remove all containers, images, and volumes
	docker-compose down -v
	docker system prune -f

ps: ## Show running containers
	docker-compose ps
