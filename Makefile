.PHONY: dev build up down destroy

dev:
	poetry run uvicorn --host=127.0.0.1 src.main:app

build:
	docker compose build

up:
	docker compose up 

down:
	docker compose down

destroy:
	docker compose down -v