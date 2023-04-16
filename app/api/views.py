import datetime

from knox.models import AuthToken
from rest_framework import status, permissions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from base.models import Restaurant, Vote, WinnerRestaurant
from api.serializers import RegisterUserSerializer, RestaurantSerializer, WinnerRestaurantSerializer

MAX_VOTES_PER_DAY = 3


# Create your views here.
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

    def create(self, request, *args, **kwargs):
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
        user_vote, created = Vote.objects.get_or_create(
            user=request.user,
            restaurant_id=kwargs.get('restaurant_pk'),
            date=datetime.date.today(),
            defaults={'score': 1, 'amount': 1}
        )

        if not created:
            votes_amount = Vote.objects.votes_per_day(user_id=self.request.user.id)
            if votes_amount >= MAX_VOTES_PER_DAY:
                raise ValidationError('Max votes per day exceeded')

            if user_vote.amount == 1:
                user_vote.score += 0.5
            else:
                user_vote.score += 0.25

            user_vote.amount += 1
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
