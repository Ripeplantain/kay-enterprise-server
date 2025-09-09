from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'admin', views.AdminAuthViewSet, basename='admin-auth')
router.register(r'client', views.ClientAuthViewSet, basename='client-auth')

urlpatterns = [
    path('', include(router.urls)),
    path('refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
]
