# pull official base image
FROM python:3.11.2-alpine

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIPENV_PIPFILE="/usr/src/app/Pipfile"

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc g++ python3-dev musl-dev libffi-dev

# install dependencies
COPY ./Pipfile ./Pipfile.lock /usr/src/app/
RUN pip install --upgrade pip && pip install pipenv
RUN pipenv install --system --deploy

# copy project
COPY . .
RUN chmod +x /usr/src/app/docker-entrypoint.sh