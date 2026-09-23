.PHONY: install run test lint check docker

install:
	python3 -m pip install -e '.[dev]'

run:
	python3 -m flight_bot.main

test:
	pytest -q

lint:
	ruff check .

check: lint test

docker:
	docker compose up --build

