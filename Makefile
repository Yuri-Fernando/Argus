.PHONY: help install up down seed download-olist generate-synthetic test lint fmt dq mdm mlflow-ui clean

help:
	@echo "Enterprise Customer Intelligence Platform — dev commands"
	@echo "  make install           Install Python dependencies (pip, editable)"
	@echo "  make up                Start local stack (MinIO, Postgres, MLflow) via docker-compose"
	@echo "  make down              Stop local stack"
	@echo "  make seed              Download Olist + generate all synthetic data (one command, see DATA_MODEL.md)"
	@echo "  make download-olist    Download only the Olist dataset from Kaggle"
	@echo "  make generate-synthetic  Generate only the synthetic CRM/marketing/support/web/finance/docs data"
	@echo "  make dq                Run the Great Expectations data quality suite"
	@echo "  make mdm               Run the entity resolution / golden record pipeline"
	@echo "  make test              Run unit + data tests"
	@echo "  make lint              Run ruff + mypy"
	@echo "  make mlflow-ui         Launch the local MLflow tracking UI"
	@echo "  make clean             Remove generated data and caches"

install:
	pip install -e ".[dev,pyspark,docs-pdf]"

up:
	docker compose up -d
	@echo "MinIO console: http://localhost:9001 (minioadmin/minioadmin)"
	@echo "MLflow UI:     http://localhost:5000"

down:
	docker compose down

download-olist:
	python ingestion/olist/download.py

generate-synthetic:
	python data/synthetic/generate_all.py --profile local

seed: download-olist generate-synthetic
	@echo "All datasets ready under data/raw/ and data/synthetic/ — see DATA_MODEL.md"

dq:
	python data_quality/run_checkpoint.py --suite customer_suite

mdm:
	python mdm/entity_resolution/run.py

test:
	pytest -q

lint:
	ruff check .
	mypy --ignore-missing-imports . || true

mlflow-ui:
	mlflow ui --backend-store-uri ./mlflow/mlruns --port 5000

clean:
	rm -rf data/raw/olist data/synthetic/*/*.csv data/documents/*.md data/documents/*.pdf .pytest_cache **/__pycache__
