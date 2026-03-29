.PHONY: install fetch analyze run api evaluate test lint notebook clean

install:
	pip install -r requirements.txt

fetch:
	python github/repo_fetcher.py --clone-targets

analyze:
	python pipeline/main.py --repo psf/requests

run:
	python dashboard/app.py

api:
	uvicorn api.server:app --reload --port 8000

evaluate:
	python evaluation/benchmark_runner.py

test:
	pytest tests/ -v --color=yes

lint:
	black . --line-length 100 && flake8 . --max-line-length=100

notebook:
	jupyter notebook notebooks/

clean:
	find . -name __pycache__ -exec rm -rf {} + 2>/dev/null; find . -name "*.pyc" -delete
