from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters

from authentication import models
from .models import Bus, BusTerminal
from .serializers import (
    BusListSerializer, BusDetailSerializer, BusCreateUpdateSerializer,
    BusTerminalSerializer
)

class BusTerminalFilter(django_filters.FilterSet):
    """Filter for bus terminals"""
    city = django_filters.CharFilter(field_name='city_town', lookup_expr='icontains')
    region = django_filters.ChoiceFilter(choices=BusTerminal.GHANA_REGIONS)
    terminal_type = django_filters.ChoiceFilter(choices=BusTerminal.TERMINAL_TYPES)
    has_facilities = django_filters.BooleanFilter(method='filter_has_facilities')
    
    class Meta:
        model = BusTerminal
        fields = ['city', 'region', 'terminal_type', 'is_active']
    
    def filter_has_facilities(self, queryset, name, value):
        """Filter terminals with essential facilities"""
        if value:
            return queryset.filter(
                has_waiting_area=True,
                has_restroom=True,
                has_luggage_storage=True
            )
        return queryset

class BusTerminalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bus terminals
    
    Permissions:
    - Read: Public access
    - Write: Authenticated users only
    """
    queryset = BusTerminal.objects.all()
    serializer_class = BusTerminalSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchBackend, filters.OrderingFilter]
    filterset_class = BusTerminalFilter
    search_fields = ['name', 'city_town', 'area_suburb']
    ordering_fields = ['name', 'city_town', 'region', 'created_at']
    ordering = ['region', 'city_town', 'name']

    @action(detail=False, methods=['get'])
    def regions(self, request):
        """Get all Ghana regions with terminal counts"""
        from django.db.models import Count
        
        regions = BusTerminal.objects.filter(is_active=True).values(
            'region'
        ).annotate(
            terminal_count=Count('id')
        ).order_by('region')
        
        region_data = []
        for region in regions:
            region_display = dict(BusTerminal.GHANA_REGIONS).get(region['region'])
            region_data.append({
                'code': region['region'],
                'name': region_display,
                'terminal_count': region['terminal_count']
            })
        
        return Response(region_data)

    @action(detail=False, methods=['get'])
    def cities(self, request):
        """Get all cities with terminals"""
        cities = BusTerminal.objects.filter(is_active=True).values_list(
            'city_town', flat=True
        ).distinct().order_by('city_town')
        
        return Response(list(cities))

class BusFilter(django_filters.FilterSet):
    """Filter for buses"""
    bus_type = django_filters.ChoiceFilter(choices=Bus.BUS_TYPES)
    status = django_filters.ChoiceFilter(choices=Bus.BUS_STATUS)
    has_ac = django_filters.BooleanFilter()
    has_wifi = django_filters.BooleanFilter()
    min_seats = django_filters.NumberFilter(field_name='total_seats', lookup_expr='gte')
    max_seats = django_filters.NumberFilter(field_name='total_seats', lookup_expr='lte')
    year_from = django_filters.NumberFilter(field_name='year_manufactured', lookup_expr='gte')
    year_to = django_filters.NumberFilter(field_name='year_manufactured', lookup_expr='lte')
    
    class Meta:
        model = Bus
        fields = ['bus_type', 'status', 'has_ac', 'has_wifi']

class BusViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing buses
    
    Permissions:
    - Read: Public access
    - Write: Authenticated users only
    
    Filtering:
    - bus_type, status, features, seat capacity, year
    """
    queryset = Bus.objects.filter(status__in=['active', 'maintenance'])
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchBackend, filters.OrderingFilter]
    filterset_class = BusFilter
    search_fields = ['name', 'bus_number', 'registration_number', 'make_model']
    ordering_fields = ['name', 'bus_type', 'total_seats', 'year_manufactured', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return BusListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BusCreateUpdateSerializer
        return BusDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = Bus.objects.all()
        
        # Staff can see all buses, regular users only see active ones
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(status='active')
        
        return queryset

    def perform_create(self, serializer):
        """Set available_seats equal to total_seats for new buses"""
        serializer.save(available_seats=serializer.validated_data['total_seats'])

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def maintenance(self, request, pk=None):
        """Mark bus for maintenance"""
        bus = self.get_object()
        
        if bus.status == 'active':
            bus.status = 'maintenance'
            bus.save()
            return Response({
                'success': True,
                'message': f'{bus.name} marked for maintenance'
            })
        
        return Response({
            'success': False,
            'message': 'Bus is not in active status'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activate(self, request, pk=None):
        """Activate bus from maintenance"""
        bus = self.get_object()
        
        if bus.status == 'maintenance':
            bus.status = 'active'
            bus.save()
            return Response({
                'success': True,
                'message': f'{bus.name} activated successfully'
            })
        
        return Response({
            'success': False,
            'message': 'Bus is not in maintenance status'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get bus fleet statistics"""
        from django.db.models import Count, Avg
        
        stats = Bus.objects.aggregate(
            total_buses=Count('id'),
            active_buses=Count('id', filter=models.Q(status='active')),
            maintenance_buses=Count('id', filter=models.Q(status='maintenance')),
            total_seats=models.Sum('total_seats'),
            avg_seats=Avg('total_seats'),
            buses_with_ac=Count('id', filter=models.Q(has_ac=True)),
            buses_with_wifi=Count('id', filter=models.Q(has_wifi=True))
        )
        
        return Response(stats)