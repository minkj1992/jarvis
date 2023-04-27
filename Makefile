.PHONY: dev build up down destroy app-shell redis-shell deploy prod-up prod-down

dev:
	poetry run uvicorn --host=127.0.0.1 main:app

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

destroy:
	docker compose down -v

deploy:
	docker compose -f docker-compose.prod.yml build
	docker compose -f docker-compose.prod.yml push

prod-up:
	docker context use jarvis0context
	docker compose -f docker-compose.prod.yml up
	docker logs jarvis0api

prod-down:
	docker context use jarvis0context
	docker compose -f docker-compose.prod.yml down
	docker context use default

app-shell:
	docker exec -it jarvis-app-1 sh

redis-shell:
	docker exec -it \
		jarvis-redis-1 \
		/bin/bash -ci 'redis-cli'
