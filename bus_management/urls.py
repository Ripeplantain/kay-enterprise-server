from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'terminals', views.BusTerminalViewSet, basename='bus-terminals')
router.register(r'buses', views.BusViewSet, basename='buses')

urlpatterns = [
    path('', include(router.urls)),
]