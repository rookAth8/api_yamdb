from rest_framework.routers import DefaultRouter
from django.urls import include, path

from api.views import signup, token

router = DefaultRouter()
# router.register('users', PostViewSet, basename='users')

urlpatterns = [
    path('v1/auth/signup/', signup, name='signup'),
    path('v1/auth/token/', token, name='token')
]
