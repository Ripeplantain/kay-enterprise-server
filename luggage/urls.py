from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'types', views.LuggageTypeViewSet, basename='luggage-types')
router.register(r'items', views.LuggageViewSet, basename='luggage-items')
router.register(r'tracking', views.LuggageTrackingViewSet, basename='luggage-tracking')

urlpatterns = [
    path('', include(router.urls)),
]