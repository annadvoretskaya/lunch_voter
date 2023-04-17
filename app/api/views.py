import datetime

from constance import config
from knox.models import AuthToken
from rest_framework import status, permissions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView, ListAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.utils import determine_vote_weight
from base import constants
from base.models import Restaurant, Vote, WinnerRestaurant
from api.serializers import RegisterUserSerializer, RestaurantSerializer, WinnerRestaurantSerializer


class RegisterView(GenericAPIView):
    serializer_class = RegisterUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _, auth_token = AuthToken.objects.create(user)
        return Response({"token": auth_token}, status=status.HTTP_201_CREATED)


class LoginView(GenericAPIView):
    permission_classes = (permissions.AllowAny, )
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        _, auth_token = AuthToken.objects.create(user)
        return Response({"token": auth_token}, status=status.HTTP_200_OK)


class RestaurantsViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, ]
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer


class VotesViewSet(GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, ]

    def create(self, request, *args, **kwargs):
        if constants.LUNCH_HOUR and datetime.datetime.now().hour >= constants.LUNCH_HOUR:
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        restaurant = get_object_or_404(Restaurant, pk=kwargs.get('restaurant_pk'))

        user_vote, created = Vote.objects.get_or_create(
            user=request.user,
            restaurant=restaurant,
            date=datetime.date.today(),
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


class WinnersListView(ListAPIView):
    serializer_class = WinnerRestaurantSerializer
    queryset = WinnerRestaurant.objects.all()

    def filter_queryset(self, queryset):
        filter_date = self.request.query_params.get('date')
        if not filter_date:
            filter_date = datetime.date.today()
        else:
            try:
                filter_date = datetime.datetime.strptime(filter_date, '%Y-%m-%d')
            except ValueError:
                raise ValidationError('Invalid date format')

        return self.queryset.filter(date=filter_date)
