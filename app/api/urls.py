import knox.views

from django.urls import include, path
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from api import views

schema_view = get_schema_view(
    openapi.Info(
        title="Lunch voter REST API",
        default_version='v1',
        description="Base url: localhost:8000/api/",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="anja.dvr@gmail.com"),

    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

logout_view = \
   swagger_auto_schema(
      method='post',
      responses={status.HTTP_204_NO_CONTENT: ''}
   )(knox.views.LogoutView.as_view())

router = DefaultRouter()
router.register(r'restaurants', views.RestaurantsViewSet, basename='restaurants')

votes_router = nested_routers.NestedSimpleRouter(router, 'restaurants', lookup='restaurant')
votes_router.register(r'votes', views.VotesViewSet, basename='votes')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(votes_router.urls)),
    path('winners/', views.WinnersListView.as_view(), name='winners-list'),
    path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', logout_view),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
