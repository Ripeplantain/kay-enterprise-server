from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.utils import timezone
from django.db import models
from .models import Payment
from booking.models import Booking
from .serializers import PaymentListSerializer, PaymentDetailSerializer, PaymentCreateSerializer

class PaymentFilter(django_filters.FilterSet):
    """Filter for payments"""
    booking = django_filters.ModelChoiceFilter(queryset=Booking.objects.all())
    booking_reference = django_filters.CharFilter(
        field_name='booking__booking_reference',
        lookup_expr='icontains'
    )
    payment_method = django_filters.ChoiceFilter(choices=Payment.payment_method)
    mobile_money_provider = django_filters.ChoiceFilter(choices=Payment.mobile_money_provider)
    status = django_filters.ChoiceFilter(choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ])
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    created_date = django_filters.DateFilter(field_name='created_at__date')
    created_from = django_filters.DateFilter(field_name='created_at__date', lookup_expr='gte')
    created_to = django_filters.DateFilter(field_name='created_at__date', lookup_expr='lte')
    
    class Meta:
        model = Payment
        fields = ['payment_method', 'mobile_money_provider', 'status']

class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments
    
    Permissions:
    - Read/Write: Authenticated users only (own payments + staff see all)
    
    Filtering:
    - booking, payment_method, provider, status, amount range, dates
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = [
        'payment_reference', 'booking__booking_reference',
        'booking__passenger_name', 'mobile_money_number'
    ]
    ordering_fields = ['created_at', 'amount', 'status', 'processed_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter payments based on user permissions"""
        if self.request.user.is_staff:
            return Payment.objects.all()
        else:
            # Regular users only see payments from their bookings
            return Payment.objects.filter(booking__client=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PaymentListSerializer
        elif self.action == 'create':
            return PaymentCreateSerializer
        return PaymentDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create payment with validation"""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Check if user owns the booking
            booking = serializer.validated_data['booking']
            if not request.user.is_staff and booking.client != request.user:
                return Response({
                    'success': False,
                    'message': 'You can only create payments for your own bookings'
                })
            
            payment = serializer.save()
            
            # Update booking payment status
            if payment.status == 'successful':
                booking.payment_status = 'paid'
                booking.booking_status = 'confirmed'
                booking.save()
            
            return Response({
                'success': True,
                'message': 'Payment created successfully',
                'payment': PaymentDetailSerializer(payment).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Payment creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process payment (simulate payment gateway response)"""
        payment = self.get_object()
        
        if payment.status != 'pending':
            return Response({
                'success': False,
                'message': f'Payment is already {payment.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simulate payment processing
        gateway_response = request.data.get('gateway_response', {})
        payment_successful = gateway_response.get('success', False)
        
        if payment_successful:
            payment.status = 'successful'
            payment.processed_at = timezone.now()
            payment.gateway_response = gateway_response
            payment.gateway_reference = gateway_response.get('reference', '')
            
            # Update booking status
            booking = payment.booking
            booking.payment_status = 'paid'
            booking.booking_status = 'confirmed'
            booking.save()
            
            message = 'Payment processed successfully'
        else:
            payment.status = 'failed'
            payment.processed_at = timezone.now()
            payment.gateway_response = gateway_response
            payment.notes = gateway_response.get('error_message', 'Payment failed')
            message = 'Payment processing failed'
        
        payment.save()
        
        return Response({
            'success': payment_successful,
            'message': message,
            'payment': PaymentDetailSerializer(payment).data
        })

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Process payment refund"""
        payment = self.get_object()
        
        if payment.status != 'successful':
            return Response({
                'success': False,
                'message': 'Only successful payments can be refunded'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refund_reason = request.data.get('reason', 'Customer request')
        
        # Process refund
        payment.status = 'refunded'
        payment.processed_at = timezone.now()
        payment.notes = f"Refunded: {refund_reason}"
        payment.save()
        
        # Update booking status
        booking = payment.booking
        booking.payment_status = 'refunded'
        booking.booking_status = 'refunded'
        booking.save()
        
        # Return seats to trip availability
        trip = booking.trip
        trip.available_seats += booking.number_of_seats
        trip.save()
        
        return Response({
            'success': True,
            'message': 'Payment refunded successfully',
            'payment': PaymentDetailSerializer(payment).data
        })

    @action(detail=False, methods=['get'])
    def my_stats(self, request):
        """Get payment statistics for current user"""
        queryset = self.get_queryset()
        
        from django.db.models import Count, Sum, Avg
        
        stats = queryset.aggregate(
            total_payments=Count('id'),
            total_amount=Sum('amount'),
            avg_amount=Avg('amount'),
            successful_payments=Count('id', filter=models.Q(status='successful')),
            failed_payments=Count('id', filter=models.Q(status='failed')),
            pending_payments=Count('id', filter=models.Q(status='pending'))
        )
        
        # Payment method breakdown
        payment_methods = queryset.values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')
        
        # Mobile money provider breakdown
        mobile_money_stats = queryset.filter(
            payment_method='mobile_money'
        ).values('mobile_money_provider').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')
        
        stats['payment_methods'] = list(payment_methods)
        stats['mobile_money_providers'] = list(mobile_money_stats)
        
        return Response({
            'success': True,
            'message': 'Payment statistics retrieved successfully',
            'stats': stats
        })

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent payments for dashboard"""
        queryset = self.get_queryset()
        recent_payments = queryset.order_by('-created_at')[:10]
        
        serializer = PaymentListSerializer(recent_payments, many=True)
        return Response({
            'success': True,
            'message': 'Recent payments retrieved successfully',
            'payments': serializer.data
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending(self, request):
        """Get pending payments that need attention"""
        queryset = self.get_queryset().filter(status='pending')
        
        # Filter by payment deadline (payments older than 2 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        deadline = timezone.now() - timedelta(hours=2)
        overdue_payments = queryset.filter(created_at__lt=deadline)
        
        serializer = PaymentListSerializer(overdue_payments, many=True)
        return Response({
            'success': True,
            'message': 'Pending payments retrieved successfully',
            'payments': serializer.data,
            'count': overdue_payments.count()
        })

    @action(detail=False, methods=['post'])
    def retry_failed(self, request):
        """Retry failed payments"""
        payment_ids = request.data.get('payment_ids', [])
        
        if not payment_ids:
            return Response({
                'success': False,
                'message': 'Payment IDs are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get failed payments that belong to the user
        failed_payments = self.get_queryset().filter(
            id__in=payment_ids,
            status='failed'
        )
        
        if not failed_payments.exists():
            return Response({
                'success': False,
                'message': 'No failed payments found to retry'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Reset payments to pending status
        updated_count = failed_payments.update(
            status='pending',
            processed_at=None,
            gateway_response=None,
            notes='Payment retry initiated'
        )
        
        return Response({
            'success': True,
            'message': f'{updated_count} payments queued for retry',
            'updated_payments': updated_count
        })
