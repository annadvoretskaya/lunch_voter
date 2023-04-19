import datetime

from constance import config
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from knox.models import AuthToken
from rest_framework import status, permissions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView, ListAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.utils import determine_vote_weight
from base.models import Restaurant, Vote, WinnerRestaurant
from api.serializers import (AuthResponseSerializer, RegisterUserSerializer,
                             RestaurantSerializer, WinnerRestaurantSerializer)


class RegisterView(GenericAPIView):
    serializer_class = RegisterUserSerializer

    @swagger_auto_schema(
        security=[],
        responses={
            status.HTTP_201_CREATED: AuthResponseSerializer,
            status.HTTP_400_BAD_REQUEST: 'Not all required fields were provided',
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _, auth_token = AuthToken.objects.create(user)
        return Response(AuthResponseSerializer({"token": auth_token}).data, status=status.HTTP_201_CREATED)


class LoginView(GenericAPIView):
    permission_classes = [permissions.AllowAny, ]
    serializer_class = AuthTokenSerializer

    @swagger_auto_schema(
        security=[],
        responses={
            status.HTTP_201_CREATED: AuthResponseSerializer,
            status.HTTP_400_BAD_REQUEST: 'Not all required fields were provided or credentials are invalid',
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        _, auth_token = AuthToken.objects.create(user)
        return Response(AuthResponseSerializer({"token": auth_token}).data, status=status.HTTP_200_OK)


@method_decorator(name='list', decorator=swagger_auto_schema(security=[]))
class RestaurantsViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, ]
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer


class VotesViewSet(GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, ]

    def get_serializer(self, *args, **kwargs):
        return

    @swagger_auto_schema(
        responses={
            status.HTTP_400_BAD_REQUEST: 'Max votes per day exceeded',
            status.HTTP_404_NOT_FOUND: 'Restaurant was not found'
        },
        operation_description='Left the vote for the restaurant',
        manual_parameters=[openapi.Parameter("restaurant_pk",
                                             openapi.IN_PATH,
                                             description="Restaurant id",
                                             type=openapi.TYPE_INTEGER
                                             )]
    )
    def create(self, request, *args, **kwargs):
        restaurant = get_object_or_404(Restaurant, pk=kwargs.get('restaurant_pk'))

        user_vote, created = Vote.objects.get_or_create(
            user=request.user,
            restaurant=restaurant,
            defaults={'score': config.VOTES_WEIGHTS[0], 'amount': 1}
        )

        if not created:
            votes_amount = Vote.objects.votes_per_day(user_id=self.request.user.id)
            if votes_amount >= config.MAX_VOTES_PER_DAY:
                raise ValidationError('Max votes per day exceeded')

            user_vote.amount += 1
            user_vote.score += determine_vote_weight(config.VOTES_WEIGHTS, user_vote.amount)
            user_vote.save(update_fields=('score', 'amount'))

        return Response(data={}, status=status.HTTP_201_CREATED)


@method_decorator(name='get', decorator=swagger_auto_schema(
    security=[],
    operation_description='Get the list of the winning restaurants by date '
                          'passed as "date" query parameter.'
                          'If "date" was not provided winners of the previous day will be returned by default',
    responses={
        status.HTTP_400_BAD_REQUEST: 'Invalid date format'
    },
    manual_parameters=[openapi.Parameter("date",
                                         openapi.IN_QUERY,
                                         description="Date in format %Y-%m-%d",
                                         type=openapi.TYPE_STRING
                                         )]
))
class WinnersListView(ListAPIView):
    permission_classes = [permissions.AllowAny, ]
    serializer_class = WinnerRestaurantSerializer
    queryset = WinnerRestaurant.objects.all()

    def filter_queryset(self, queryset):
        filter_date = self.request.query_params.get('date')
        if not filter_date:
            filter_date = datetime.date.today() - datetime.timedelta(days=1)
        else:
            try:
                filter_date = datetime.datetime.strptime(filter_date, '%Y-%m-%d')
            except ValueError:
                raise ValidationError('Invalid date format')

        return self.queryset.filter(date=filter_date)
