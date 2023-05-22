.PHONY: dev build up down destroy app-shell redis-shell push deploy ssh info p-info

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
	docker compose --file docker-compose.prod.yml down
	docker compose --file docker-compose.prod.yml up --build -d --remove-orphans

app-shell:
	docker exec -it jarvis-app-1 sh

redis-shell:
	docker exec -it \
		jarvis-redis \
		/bin/bash -ci 'redis-cli --raw'

ssh:
	gcloud compute ssh jarvis-ins

info:
	docker compose logs -f

p-info:
	docker compose --file docker-compose.prod.yml logs -f