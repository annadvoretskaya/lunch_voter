import datetime
from unittest import mock

from django.test import TestCase
from django.contrib.auth.models import User

from base.models import Restaurant, Vote, WinnerRestaurant
from base.tasks import determine_winner


class DetermineTodayWinnerTestCase(TestCase):
    fixtures = ['fixtures/tests/users.json', 'fixtures/tests/restaurants.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.first()
        cls.restaurants = Restaurant.objects.all()

    def test_determine_winner(self):
        Vote.objects.create(user=self.user, restaurant=self.restaurants[0], score=4, amount=2)
        Vote.objects.create(user=self.user, restaurant=self.restaurants[1], score=2, amount=1)

        with mock.patch('base.tasks.datetime', wraps=datetime) as mock_datetime:
            mock_datetime.date.today.return_value = datetime.date.today() + datetime.timedelta(days=1)

            determine_winner()

            winner_restaurant = WinnerRestaurant.objects.filter(date=datetime.date.today()).first()
            self.assertIsNotNone(winner_restaurant)
            self.assertEqual(winner_restaurant.restaurant, self.restaurants[0])
            self.assertEqual(winner_restaurant.score, 4.0)
            self.assertEqual(winner_restaurant.unique_voters, 1)

    def test_determine_winner_no_votes(self):
        determine_winner()

        winner_restaurant = WinnerRestaurant.objects.filter(date=datetime.date.today()).first()
        self.assertIsNone(winner_restaurant)

    def test_determine_winner_equal_scores(self):
        vote_date = datetime.date.today()
        users = User.objects.all()

        Vote.objects.create(user=users[0], restaurant=self.restaurants[0], date=vote_date, score=3, amount=3)
        Vote.objects.create(user=users[1], restaurant=self.restaurants[0], date=vote_date, score=1, amount=1)

        Vote.objects.create(user=users[0], restaurant=self.restaurants[1], date=vote_date, score=1, amount=1)
        Vote.objects.create(user=users[1], restaurant=self.restaurants[1], date=vote_date, score=1, amount=1)
        Vote.objects.create(user=users[2], restaurant=self.restaurants[1], date=vote_date, score=2, amount=2)

        with mock.patch('base.tasks.datetime', wraps=datetime) as mock_datetime:
            mock_datetime.date.today.return_value = datetime.date.today() + datetime.timedelta(days=1)
            determine_winner()

            winners = WinnerRestaurant.objects.filter(date=vote_date)
            self.assertIsNotNone(winners)
            self.assertEqual(len(winners), 1)

            winner = winners.first()
            self.assertEqual(winner.restaurant, self.restaurants[1])
            self.assertEqual(winner.score, 4.0)
            self.assertEqual(winner.unique_voters, 3)

    def test_determine_winner_multiple_winners(self):
        vote_date = datetime.date.today()
        users = User.objects.all()

        for i, restaurant in enumerate(self.restaurants):
            for user in users:
                Vote.objects.create(
                    user=user,
                    restaurant=restaurant,
                    date=vote_date,
                    score=1,
                    amount=1
                )

        with mock.patch('base.tasks.datetime', wraps=datetime) as mock_datetime:
            mock_datetime.date.today.return_value = datetime.date.today() + datetime.timedelta(days=1)

            determine_winner()

            winners = WinnerRestaurant.objects.filter(date=vote_date)
            self.assertIsNotNone(winners)
            self.assertEqual(len(winners), 3)
            self.assertEqual(
                [winner.restaurant for winner in winners.order_by('restaurant_id')],
                list(self.restaurants.order_by('id'))
            )

            for winner in winners:
                self.assertEqual(winner.score, 3.0)
                self.assertEqual(winner.unique_voters, 3)
