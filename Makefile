.PHONY: dev build up down destroy app-shell redis-shell push deploy prod-down

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

push:
	az login
	docker login jarvisgptacr.azurecr.io
	docker compose -f docker-compose.prod.yml push

deploy:
	az login
	docker login jarvisgptacr.azurecr.io
	docker context use jarvis0context
	docker compose --file docker-compose.prod.yml up --build
	docker logs --file jarvis_jarvis0api

prod-down:
	docker context use jarvis0context
	docker compose --file docker-compose.prod.yml down
	docker context use default

app-shell:
	docker exec -it jarvis-app-1 sh

redis-shell:
	docker exec -it \
		jarvis_jarvis-redis \
		/bin/bash -ci 'redis-cli'


ssh:
	ssh -i jarvisVM_key.pem azureuser@20.39.184.5
