FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /src

RUN apt-get update && \
  apt-get install -y --no-install-recommends netcat && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY poetry.lock pyproject.toml /src/
RUN pip install poetry==1.4 && \
  poetry config virtualenvs.create false && \
  poetry install --no-dev --no-cache --no-ansi

COPY ./src /src
