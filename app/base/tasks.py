import datetime

from celery.schedules import crontab
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, Sum, Window

from lunch_voter.celery import app
from base import constants
from base.models import Vote, WinnerRestaurant


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute=0, hour=constants.LUNCH_HOUR),
        determine_today_winner.s()
    )


@app.task
def determine_today_winner():
    date = datetime.date.today()

    vote_results = Vote.objects.filter(date=date)\
        .values('restaurant_id')\
        .annotate(
            score_sum=Sum('score'),
            users_count=Count('user_id'),
            restaurants_ids=Window(
                expression=ArrayAgg('restaurant_id'),
                partition_by=['score_sum', 'users_count'],
                order_by=['-score_sum', '-users_count']
            )
        )\
        .values('score_sum', 'users_count', 'restaurants_ids')\
        .order_by('-score_sum', '-users_count')\
        .first()

    if vote_results:
        winner_results = (
            WinnerRestaurant(
                restaurant_id=rest_id,
                score=vote_results['score_sum'],
                unique_voters=vote_results['users_count']
            )
            for rest_id in vote_results['restaurants_ids']
        )

        WinnerRestaurant.objects.bulk_create(winner_results)
