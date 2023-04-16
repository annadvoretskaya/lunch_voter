import knox.views

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from api import views

router = DefaultRouter()
router.register(r'restaurants', views.RestaurantsViewSet, basename='restaurants')

votes_router = nested_routers.NestedSimpleRouter(router, 'restaurants', lookup='restaurant')
votes_router.register(r'votes', views.VotesViewSet, basename='votes')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(votes_router.urls)),
    path('winners/', views.WinnersListView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', knox.views.LogoutView.as_view())
]
