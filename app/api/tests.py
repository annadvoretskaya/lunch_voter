import datetime

from constance.test import override_config
from django.contrib.auth.models import User
from knox.models import AuthToken
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from unittest import mock

from api.serializers import WinnerRestaurantSerializer
from base import constants
from base.models import Restaurant, Vote, WinnerRestaurant


class RegisterViewTestCase(APITestCase):
    def test_register_user(self):
        # url = reverse('register')
        data = {
            'username': 'test_user',
            'email': 'test_user@example.com',
            'password': 'test_pass'
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_missed_fields(self):
        data = {'username': 'test_user'}
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'password': 'test_pass'}
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_user(self):
        User.objects.create_user(username='test_user', password='test_pass')
        data = {'username': 'test_user', 'password': '123456'}
        response = self.client.post('/api/register/', data)


class LoginViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test_user@example.com',
            password='test_pass'
        )

    def test_login_user(self):
        data = {
            'username': 'test_user',
            'password': 'test_pass'
        }
        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_invalid_credentials(self):
        data = {'username': 'test_user', 'password': 'wrong_password'}
        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        _, self.token = AuthToken.objects.create(self.user)

    def test_logout_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post('/api/logout/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_without_token(self):
        response = self.client.post('/api/logout/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer invalid_token')
        response = self.client.post('/api/logout/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RestaurantsViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test_user@example.com',
            password='test_pass'
        )
        self.restaurant = Restaurant.objects.create(name='Test Restaurant')

    def test_list_restaurants(self):
        url = reverse('restaurants-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_restaurant(self):
        data = {'name': 'New Restaurant'}
        self.client.force_authenticate(user=self.user)
        url = reverse('restaurants-list')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Restaurant.objects.count(), 2)
        self.assertEqual(response.data['name'], data['name'])

    def test_update_restaurant(self):
        url = reverse('restaurants-detail', args=[self.restaurant.id])
        data = {
            'name': 'Updated Restaurant'
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.name, data['name'])

    def test_delete_restaurant(self):
        url = reverse('restaurants-detail', args=[self.restaurant.id])
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Restaurant.objects.count(), 0)


class VotesViewSetTestCase(APITestCase):
    fixtures = ['fixtures/tests/users.json', 'fixtures/tests/restaurants.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.first()
        cls.restaurants = Restaurant.objects.all()

    @mock.patch('api.views.datetime', wraps=datetime)
    def test_create_vote(self, mock_datetime):
        vote_hour = constants.LUNCH_HOUR - 1
        mock_datetime.datetime.now.return_value = datetime.datetime.now().replace(hour=vote_hour)
        url = reverse('votes-list', args=[self.restaurants[1].id])
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().score, 1)

    @mock.patch('base.constants.LUNCH_HOUR', 0)
    def test_create_vote_all_day(self):
        url = reverse('votes-list', args=[self.restaurants[1].id])
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().score, 1)

    @mock.patch('api.views.datetime', wraps=datetime)
    def test_create_vote_too_late(self, mock_datetime):
        vote_hour = constants.LUNCH_HOUR + 1
        mock_datetime.datetime.now.return_value = datetime.datetime.now().replace(hour=vote_hour)
        url = reverse('votes-list', args=[self.restaurants[1].id])
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @mock.patch('api.views.datetime', wraps=datetime)
    @override_config(MAX_VOTES_PER_DAY=4)
    def test_create_multiple_votes_same_restaurant(self, mock_datetime):
        vote_hour = constants.LUNCH_HOUR - 1
        mock_datetime.datetime.now.return_value = datetime.datetime.now().replace(hour=vote_hour)

        date = datetime.date.today()
        url = reverse('votes-list', args=[self.restaurants[1].id])
        self.client.force_authenticate(user=self.user)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vote = Vote.objects.get(user=self.user, restaurant=self.restaurants[1], date=date)
        self.assertEqual(vote.score, 1.0)
        self.assertEqual(vote.amount, 1)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vote = Vote.objects.get(user=self.user, restaurant=self.restaurants[1], date=date)
        self.assertEqual(vote.score, 1.5)
        self.assertEqual(vote.amount, 2)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vote = Vote.objects.get(user=self.user, restaurant=self.restaurants[1], date=date)
        self.assertEqual(vote.score, 1.75)
        self.assertEqual(vote.amount, 3)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vote = Vote.objects.get(user=self.user, restaurant=self.restaurants[1], date=date)
        self.assertEqual(vote.score, 2.0)
        self.assertEqual(vote.amount, 4)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('api.views.datetime', wraps=datetime)
    @override_config(VOTES_WEIGHTS=[2.0, 1.5])
    def test_create_vote_another_votes_weights(self, mock_datetime):
        vote_hour = constants.LUNCH_HOUR - 1
        mock_datetime.datetime.now.return_value = datetime.datetime.now().replace(hour=vote_hour)

        date = datetime.date.today()
        url = reverse('votes-list', args=[self.restaurants[1].id])
        self.client.force_authenticate(user=self.user)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vote = Vote.objects.get(user=self.user, restaurant=self.restaurants[1], date=date)
        self.assertEqual(vote.score, 2.0)
        self.assertEqual(vote.amount, 1)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vote = Vote.objects.get(user=self.user, restaurant=self.restaurants[1], date=date)
        self.assertEqual(vote.score, 3.5)
        self.assertEqual(vote.amount, 2)

    @mock.patch('api.views.datetime', wraps=datetime)
    @override_config(MAX_VOTES_PER_DAY=2)
    def test_create_vote_different_restaurants(self, mock_datetime):
        vote_hour = constants.LUNCH_HOUR - 1
        mock_datetime.datetime.now.return_value = datetime.datetime.now().replace(hour=vote_hour)

        date = datetime.date.today()
        url_1 = reverse('votes-list', args=[self.restaurants[0].id])
        url_2 = reverse('votes-list', args=[self.restaurants[1].id])
        self.client.force_authenticate(user=self.user)

        response = self.client.post(url_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vote = Vote.objects.get(user=self.user, restaurant=self.restaurants[0], date=date)
        self.assertEqual(vote.score, 1.0)
        self.assertEqual(vote.amount, 1)

        response = self.client.post(url_2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vote = Vote.objects.get(user=self.user, restaurant=self.restaurants[1], date=date)
        self.assertEqual(vote.score, 1.0)
        self.assertEqual(vote.amount, 1)

        response = self.client.post(url_1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_vote_unauthenticated(self):
        url = reverse('votes-list', kwargs={'restaurant_pk': self.restaurants[1].id})
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('api.views.datetime', wraps=datetime)
    def test_create_vote_invalid_restaurant(self, mock_datetime):
        vote_hour = constants.LUNCH_HOUR - 1
        mock_datetime.datetime.now.return_value = datetime.datetime.now().replace(hour=vote_hour)
        self.client.force_authenticate(user=self.user)
        url = reverse('votes-list', kwargs={'restaurant_pk': 999})
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WinnersListViewTestCase(APITestCase):
    fixtures = ['fixtures/tests/users.json', 'fixtures/tests/restaurants.json', 'fixtures/tests/winners.json']

    @classmethod
    def setUpTestData(cls):
        cls.restaurant = Restaurant.objects.first()
        cls.winner = WinnerRestaurant.objects.create(
            restaurant=cls.restaurant,
            score=4.5,
            unique_voters=3
        )

    def test_get_winners(self):
        url = reverse('winners-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        serialized_winner = WinnerRestaurantSerializer(self.winner)
        self.assertEqual(response.data[0], serialized_winner.data)

    def test_filter_by_date(self):
        url = f"{reverse('winners-list')}?date={self.winner.date}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        serialized_winner = WinnerRestaurantSerializer(self.winner)
        self.assertEqual(response.data[0], serialized_winner.data)

        url = f"{reverse('winners-list')}?date=2023-04-16"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_invalid_date_format(self):
        url = f"{reverse('winners-list')}?date=2022-04-16T00:00:00Z"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data[0]), 'Invalid date format')
