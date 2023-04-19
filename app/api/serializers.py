from django.contrib.auth.models import User
from rest_framework import serializers
from knox.settings import knox_settings

from base.models import Restaurant, WinnerRestaurant


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class AuthResponseSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=knox_settings.AUTH_TOKEN_CHARACTER_LENGTH)


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = '__all__'


class WinnerRestaurantSerializer(serializers.ModelSerializer):
    restaurant = RestaurantSerializer()

    class Meta:
        model = WinnerRestaurant
        fields = ('restaurant', 'score', 'unique_voters')
