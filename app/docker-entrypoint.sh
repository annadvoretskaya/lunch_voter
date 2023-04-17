#!/bin/sh


./manage.py migrate
./manage.py createsuperuser --noinput
./manage.py runserver 0.0.0.0:8000
