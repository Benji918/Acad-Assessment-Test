PYTHON = python
MANAGE = $(PYTHON) manage.py

runserver: ## Run Django server
	$(MANAGE) runserver 0.0.0.0:8000

migrate: ## Apply database migrations
	$(MANAGE) migrate

makemigrations: ## Create new migrations
	$(MANAGE) makemigrations

# Celery workers
celery-worker: ## Start Celery worker
	celery -A choppr worker -l info

celery-beat: ## Start Celery beat scheduler
	celery -A choppr beat -l info

# Redis
redis-start: ## Run Redis locally
	redis-server

# Testing & linting
test: ## Run Django tests
	$(MANAGE) test


# Clean up junk files
clean: ## Remove __pycache__ and .pyc files
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

# Help menu for teammates
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
