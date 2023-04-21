.PHONY: dev build up down destroy app-shell redis-shell

dev:
	poetry run uvicorn --host=127.0.0.1 src.main:app

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

destroy:
	docker compose down -v

app-shell:
	docker exec -it jarvis-app-1 sh

redis-shell:
	docker exec -it \
		jarvis-redis-1 \
		/bin/bash -ci 'redis-cli'
