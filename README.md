# A Lunch-Voter REST API

A simple REST API for choosing where to go to lunch.
The API provides ability to:
 - register/login/logout
 - create/update/delete/list restaurants
 - vote for the restaurants
 - list the winners of the day

The assumptions that were made: all app users live in the same area in the same timezone (UTC by default).
User's votes accepts during the whole day, the results will be calculated at 00:00 UTC 

## Tech stack
- Python 3.11
- Django 4.2
- Django-rest-framework 3.14.0
- Celery 5.2.7
- Postgresql 14.0
- Redis 7.0

## Launch the app

----------------------------------
    1. Install docker+docker-compose https://www.docker.com/
    
    2. Clone the repo

    3. Run docker-compose up -d --build

    4. To run the tests: docker-compose exec app ./manage.py test
        

## API 

You can find API docs [here](http://localhost:8000/api/redoc/) after launching the app

