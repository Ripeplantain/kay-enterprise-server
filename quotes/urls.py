from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    path('request/', views.request_bus_quote, name='request'),
]