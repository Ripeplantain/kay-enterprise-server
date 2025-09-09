from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'routes', views.RouteViewSet, basename='routes')
router.register(r'trips', views.TripViewSet, basename='trips')
router.register(r'luggage-types', views.LuggageTypeViewSet, basename='luggage-types')
router.register(r'bookings', views.BookingViewSet, basename='bookings')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', views.SearchTripsView.as_view({'get': 'search'}), name='search-trips'),
]