# https://github.com/orgs/python-poetry/discussions/1879#discussioncomment-216865
FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && \
  apt-get install -y --no-install-recommends netcat && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY poetry.lock pyproject.toml ./

RUN pip install poetry==1.4 && \
  poetry config virtualenvs.in-project true && \
  poetry install --no-dev


COPY . ./
CMD poetry run uvicorn --host=0.0.0.0 app.main:app


# jarvis-app-1 exited with code 1
# jarvis-app-1    | Command not found: uvicorn
