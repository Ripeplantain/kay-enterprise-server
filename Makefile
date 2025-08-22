# Makefile for Django project

# Variables
PYTHON = python3
PIP = pip
MANAGE = $(PYTHON) manage.py
VENV = venv

.PHONY: help
help:
	@echo "Django Project Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make setup           - Set up virtual environment and install dependencies"
	@echo "  make run             - Run the development server"
	@echo "  make migrate         - Apply database migrations"
	@echo "  make makemigrations  - Create new migrations based on changes"
	@echo "  make superuser       - Create a Django superuser"
	@echo "  make createuser      - Create a regular Django user"
	@echo "  make createapp       - Create a new Django app"
	@echo "  make test            - Run tests"
	@echo "  make clean           - Remove pyc and __pycache__ files"
	@echo "  make shell           - Open Django shell"
	@echo "  make collectstatic   - Collect static files"

.PHONY: setup
setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/$(PIP) install --upgrade pip
	$(VENV)/bin/$(PIP) install -r requirements.txt

.PHONY: run
run:
	$(MANAGE) runserver

.PHONY: makemigrations
makemigrations:
	$(MANAGE) makemigrations

.PHONY: migrate
migrate:
	$(MANAGE) migrate

.PHONY: superuser
superuser:
	$(MANAGE) createsuperuser

.PHONY: createuser
createuser:
	@read -p "Username: " username; \
	read -p "Email: " email; \
	read -s -p "Password: " password; \
	echo ""; \
	$(MANAGE) shell -c "from django.contrib.auth.models import User; User.objects.create_user(username='$$username', email='$$email', password='$$password')"; \
	echo "User $$username created successfully."

.PHONY: createapp
createapp:
	@read -p "App name: " appname; \
	$(MANAGE) startapp $$appname; \
	echo "App $$appname created successfully."

.PHONY: test
test:
	$(MANAGE) test

.PHONY: clean
clean:
	find . -name "*.pyc" -exec rm -f {} \;
	find . -name "__pycache__" -exec rm -rf {} \;

.PHONY: shell
shell:
	$(MANAGE) shell

.PHONY: collectstatic
collectstatic:
	$(MANAGE) collectstatic --noinput
