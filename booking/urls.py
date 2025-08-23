from booking.views import RouteViewSet, TripViewSet, BookingViewSet
from rest_framework.routers import DefaultRouter
from authentication.urls import urlpatterns

router = DefaultRouter()

router.register(r'routes', RouteViewSet, basename='routes')
router.register(r'trips', TripViewSet, basename='trips')
router.register(r'bookings', BookingViewSet, basename='bookings')

urlpatterns += router.urls