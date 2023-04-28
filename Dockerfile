# https://fastapi.tiangolo.com/deployment/docker/#docker-image-with-poetry
FROM python:3.8-slim as requirements-stage

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /tmp

RUN apt-get update && \
  apt-get install -y --no-install-recommends netcat && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./poetry.lock* ./pyproject.toml /tmp/
RUN pip install poetry==1.4
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.8-slim

WORKDIR /src

COPY --from=requirements-stage /tmp/requirements.txt /src/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /src/requirements.txt


EXPOSE 80
EXPOSE 443

COPY ./src /src/
