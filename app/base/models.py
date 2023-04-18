import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum


class Restaurant(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)


class VoteManager(models.Manager):
    def votes_per_day(self, user_id: int, date: datetime.date = None) -> int:
        if not date:
            date = datetime.date.today()
        return self.filter(user_id=user_id, date=date).aggregate(votes_amount=Sum('amount'))['votes_amount']


class Vote(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    score = models.FloatField()
    amount = models.IntegerField()
    date = models.DateField(auto_now_add=True, db_index=True)

    objects = VoteManager()

    class Meta:
        unique_together = (('user', 'restaurant', 'date'), )


class WinnerRestaurant(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True, db_index=True)
    score = models.FloatField()
    unique_voters = models.IntegerField()
