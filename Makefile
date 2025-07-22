# Makefile for SMS Spam Detector

.PHONY: help install test lint format build docker-build docker-run clean setup-dev

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install dependencies"
	@echo "  test         Run all tests"
	@echo "  lint         Run code linting"
	@echo "  format       Format code with black and isort"
	@echo "  build        Build the application"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run Docker container"
	@echo "  setup-dev    Setup development environment"
	@echo "  clean        Clean up generated files"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Run tests
test:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
	coverage report --fail-under=80

# Run performance tests
test-performance:
	locust -f tests/performance/locustfile.py --headless -u 50 -r 5 -t 60s --host=http://localhost:5000

# Security testing
test-security:
	bandit -r . -f json -o reports/bandit-report.json
	safety check --json --output reports/safety-report.json

# Code linting
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	pylint app.py model.py

# Format code
format:
	black . --line-length 88
	isort . --profile black

# Build application
build:
	python -m pip install --upgrade build
	python -m build

# Docker operations
docker-build:
	docker build -t spam-detector:latest .
	docker tag spam-detector:latest spam-detector:$(shell git rev-parse --short HEAD)

docker-run:
	docker run -p 5000:5000 --env-file .env spam-detector:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down -v

# Kubernetes operations
k8s-deploy:
	kubectl apply -f k8s/
	kubectl rollout status deployment/spam-detector

k8s-delete:
	kubectl delete -f k8s/

# Helm operations
helm-install:
	helm install spam-detector ./helm --values helm/values-dev.yaml

helm-upgrade:
	helm upgrade spam-detector ./helm --values helm/values-dev.yaml

helm-uninstall:
	helm uninstall spam-detector

# Terraform operations
terraform-init:
	cd terraform && terraform init

terraform-plan:
	cd terraform && terraform plan -var-file="environments/dev.tfvars"

terraform-apply:
	cd terraform && terraform apply -var-file="environments/dev.tfvars"

terraform-destroy:
	cd terraform && terraform destroy -var-file="environments/dev.tfvars"

# Development environment setup
setup-dev:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pip install -r requirements-dev.txt
	pre-commit install
	mkdir -p logs reports

# Model training
train:
	python train_model.py

# Start development server
dev:
	FLASK_ENV=development FLASK_DEBUG=1 python app.py

# Production server
prod:
	gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# Generate documentation
docs:
	mkdocs build
	mkdocs serve

# Database migrations (if using Flask-Migrate)
db-init:
	flask db init

db-migrate:
	flask db migrate -m "$(message)"

db-upgrade:
	flask db upgrade

# Monitoring
logs:
	docker-compose logs -f app

metrics:
	curl http://localhost:5000/metrics

health:
	curl http://localhost:5000/health | jq

# Load testing
load-test:
	artillery run tests/performance/load-test.yml

# Code coverage
coverage:
	coverage run -m pytest tests/
	coverage report
	coverage html
