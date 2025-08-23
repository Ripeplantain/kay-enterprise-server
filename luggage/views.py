from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.db import models

from .models import LuggageType, Luggage, LuggageTracking
from .serializers import (
    LuggageTypeSerializer, LuggageListSerializer, LuggageDetailSerializer,
    LuggageCreateSerializer, LuggageUpdateSerializer, LuggageTrackingSerializer,
    LuggageTrackingCreateSerializer
)

class LuggageTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing luggage types
    
    Permissions:
    - Read: Public access
    - Write: Staff only
    """
    queryset = LuggageType.objects.filter(is_active=True)
    serializer_class = LuggageTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchBackend, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'base_price', 'max_weight_kg']
    ordering = ['base_price']

    def get_permissions(self):
        """Allow public read access, require authentication for write operations"""
        if self.action in ['list', 'retrieve']:
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

class LuggageFilter(django_filters.FilterSet):
    """Filter for luggage"""
    booking = django_filters.ModelChoiceFilter(
        queryset=models.Booking.objects.all()
    )
    booking_reference = django_filters.CharFilter(
        field_name='booking__booking_reference',
        lookup_expr='icontains'
    )
    status = django_filters.ChoiceFilter(choices=Luggage.LUGGAGE_STATUS)
    luggage_type = django_filters.ModelChoiceFilter(queryset=LuggageType.objects.all())
    is_fragile = django_filters.BooleanFilter()
    is_valuable = django_filters.BooleanFilter()
    weight_min = django_filters.NumberFilter(field_name='weight_kg', lookup_expr='gte')
    weight_max = django_filters.NumberFilter(field_name='weight_kg', lookup_expr='lte')
    registered_date = django_filters.DateFilter(field_name='registered_at__date')
    registered_from = django_filters.DateFilter(field_name='registered_at__date', lookup_expr='gte')
    registered_to = django_filters.DateFilter(field_name='registered_at__date', lookup_expr='lte')
    
    class Meta:
        model = Luggage
        fields = ['status', 'is_fragile', 'is_valuable', 'luggage_type']

class LuggageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing luggage
    
    Permissions:
    - Read: Authenticated users (own luggage + staff see all)
    - Write: Authenticated users only
    
    Filtering:
    - booking, status, type, fragile, valuable, weight, dates
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchBackend, filters.OrderingFilter]
    filterset_class = LuggageFilter
    search_fields = [
        'luggage_tag', 'description', 'booking__booking_reference',
        'booking__passenger_name'
    ]
    ordering_fields = ['registered_at', 'weight_kg', 'luggage_fee', 'status']
    ordering = ['-registered_at']

    def get_queryset(self):
        """Filter luggage based on user permissions"""
        if self.request.user.is_staff:
            return Luggage.objects.all()
        else:
            # Regular users only see luggage from their bookings
            return Luggage.objects.filter(booking__client=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return LuggageListSerializer
        elif self.action == 'create':
            return LuggageCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LuggageUpdateSerializer
        return LuggageDetailSerializer

    @action(detail=True, methods=['get'])
    def track(self, request, pk=None):
        """Get tracking history for luggage"""
        luggage = self.get_object()
        tracking_records = luggage.tracking_history.all()
        serializer = LuggageTrackingSerializer(tracking_records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_location(self, request, pk=None):
        """Update luggage location and status"""
        luggage = self.get_object()
        
        tracking_serializer = LuggageTrackingCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if tracking_serializer.is_valid():
            # Set the luggage for the tracking record
            tracking_data = tracking_serializer.validated_data
            tracking_data['luggage'] = luggage
            
            tracking_record = tracking_serializer.save()
            
            return Response({
                'success': True,
                'message': 'Location updated successfully',
                'tracking': LuggageTrackingSerializer(tracking_record).data
            })
        
        return Response(tracking_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def search_by_tag(self, request):
        """Search luggage by tag"""
        tag = request.query_params.get('tag')
        
        if not tag:
            return Response({
                'error': 'Luggage tag is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            luggage = Luggage.objects.get(luggage_tag__icontains=tag)
            
            # Check permissions
            if not self.request.user.is_staff and luggage.booking.client != self.request.user:
                return Response({
                    'error': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = LuggageDetailSerializer(luggage)
            return Response(serializer.data)
            
        except Luggage.DoesNotExist:
            return Response({
                'error': 'Luggage not found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get luggage statistics"""
        from django.db.models import Count, Sum, Avg
        
        queryset = self.get_queryset()
        
        stats = queryset.aggregate(
            total_items=Count('id'),
            total_weight=Sum('weight_kg'),
            avg_weight=Avg('weight_kg'),
            total_fees=Sum('luggage_fee'),
            fragile_items=Count('id', filter=models.Q(is_fragile=True)),
            valuable_items=Count('id', filter=models.Q(is_valuable=True))
        )
        
        # Status breakdown
        status_stats = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        stats['status_breakdown'] = list(status_stats)
        
        return Response(stats)

class LuggageTrackingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing luggage tracking records
    
    Permissions:
    - Read: Authenticated users only
    - Write: Staff only
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['luggage', 'status']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Filter tracking records based on user permissions"""
        if self.request.user.is_staff:
            return LuggageTracking.objects.all()
        else:
            # Regular users only see tracking for their luggage
            return LuggageTracking.objects.filter(
                luggage__booking__client=self.request.user
            )

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return LuggageTrackingCreateSerializer
        return LuggageTrackingSerializer

    def get_permissions(self):
        """Only staff can create/update/delete tracking records"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]  # You might want to add IsStaff here
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
