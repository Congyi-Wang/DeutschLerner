.PHONY: run cli test lint format docker docker-up docker-down migrate export setup

run:
	python main.py serve

cli:
	python main.py cli

cli-claude:
	python main.py cli --provider claude_cli

test:
	pytest tests/ -v --cov=src

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

docker:
	docker build -t deutsch-lerner .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	python main.py migrate

export:
	python main.py export

setup:
	bash scripts/setup.sh
