from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.db.models import Count, Sum, Max
from django.db import models

from utils.enums.auth import AuthMessage
from .models import Client
from .serializers import (
    AdminLoginSerializer,
    ClientRegistrationSerializer,
    ClientLoginSerializer,
    AdminSerializer,
    ClientSerializer,
    ClientUpdateSerializer,
    ClientListSerializer,
    ClientDetailSerializer,
)


class AdminAuthViewSet(viewsets.GenericViewSet):

    def get_serializer_class(self):
        if self.action == "login":
            return AdminLoginSerializer
        elif self.action == "profile":
            return AdminSerializer
        return None

    def get_permissions(self):
        if self.action in ["login"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            user.last_login = timezone.now()
            user.save()

            refresh = RefreshToken.for_user(user)
            refresh['user_type'] = 'admin'
            return Response(
                {
                    "success": True,
                    "message": AuthMessage.SUCCESS_ADMIN_LOGIN.value,
                    "user_type": "admin",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": AdminSerializer(user).data,
                }
            )
        return Response(
            {
                "success": False,
                "message": AuthMessage.ERROR_ADMIN_INVALID_CREDENTIALS.value,
                "errors": serializer.errors,
            }
        )

    @action(detail=False, methods=["post"])
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {
                        "success": False,
                        "message": AuthMessage.REFRESH_TOKEN_REQUIRED.value,
                    }
                )

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"success": True, "message": AuthMessage.SUCCESS_ADMIN_LOGOUT.value}
            )
        except Exception:
            return Response(
                {"success": False, "message": AuthMessage.INVALID_TOKEN.value}
            )

    @action(detail=False, methods=["get"])
    def profile(self, request):
        serializer = AdminSerializer(request.user)
        return Response(
            {
                "success": True,
                "message": AuthMessage.SUCCESS_ADMIN_PROFILE.value,
                "user": serializer.data,
            }
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def clients(self, request):
        """Get paginated list of all clients with booking statistics"""
        from rest_framework.pagination import PageNumberPagination
        
        # Get clients with booking counts and statistics
        queryset = Client.objects.annotate(
            booking_count=Count('bookings', distinct=True),
            total_bookings_amount=Sum('bookings__total_amount'),
            last_booking_date=Max('bookings__booking_date')
        ).select_related().order_by('-date_joined')
        
        # Apply filters
        filterset = ClientFilter(request.GET, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs
        
        # Apply search
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(other_names__icontains=search) |
                models.Q(phone_number__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(city_town__icontains=search)
            )
        
        # Apply ordering
        ordering = request.query_params.get('ordering', '-date_joined')
        valid_orderings = [
            'date_joined', '-date_joined', 'first_name', '-first_name',
            'last_name', '-last_name', 'booking_count', '-booking_count',
            'total_bookings_amount', '-total_bookings_amount', 'last_booking_date',
            '-last_booking_date', 'is_active', 'is_verified'
        ]
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        
        # Paginate
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))
        paginator.max_page_size = 100
        
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = ClientListSerializer(page, many=True)
            return paginator.get_paginated_response({
                'success': True,
                'message': 'Clients retrieved successfully',
                'clients': serializer.data,
                'total_count': queryset.count(),
                'filters_applied': {
                    'search': search,
                    'filters': dict(request.query_params)
                }
            })
        
        serializer = ClientListSerializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Clients retrieved successfully',
            'clients': serializer.data,
            'total_count': queryset.count()
        })

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get admin dashboard statistics"""
        from booking.models import Booking
        
        # Client statistics
        total_clients = Client.objects.count()
        active_clients = Client.objects.filter(is_active=True).count()
        verified_clients = Client.objects.filter(is_verified=True).count()
        inactive_clients = Client.objects.filter(is_active=False).count()
        
        # Booking statistics  
        total_bookings = Booking.objects.count()
        confirmed_bookings = Booking.objects.filter(booking_status='confirmed').count()
        pending_bookings = Booking.objects.filter(booking_status='pending').count()
        cancelled_bookings = Booking.objects.filter(booking_status='cancelled').count()
        
        # Additional useful stats
        clients_with_bookings = Client.objects.filter(bookings__isnull=False).distinct().count()
        clients_without_bookings = total_clients - clients_with_bookings
        
        # Recent activity (last 30 days)
        from django.utils import timezone
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        recent_clients = Client.objects.filter(date_joined__gte=thirty_days_ago).count()
        recent_bookings = Booking.objects.filter(booking_date__gte=thirty_days_ago).count()
        
        # Revenue statistics
        from django.db.models import Sum
        total_revenue = Booking.objects.filter(
            payment_status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        recent_revenue = Booking.objects.filter(
            payment_status='paid',
            booking_date__gte=thirty_days_ago
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        stats_data = {
            'clients': {
                'total': total_clients,
                'active': active_clients,
                'verified': verified_clients,
                'inactive': inactive_clients,
                'with_bookings': clients_with_bookings,
                'without_bookings': clients_without_bookings,
                'recent_signups': recent_clients
            },
            'bookings': {
                'total': total_bookings,
                'confirmed': confirmed_bookings,
                'pending': pending_bookings,
                'cancelled': cancelled_bookings,
                'recent': recent_bookings
            },
            'revenue': {
                'total': float(total_revenue),
                'recent_30_days': float(recent_revenue)
            },
            'activity': {
                'period': '30 days',
                'new_clients': recent_clients,
                'new_bookings': recent_bookings
            }
        }
        
        return Response({
            'success': True,
            'message': 'Admin statistics retrieved successfully',
            'stats': stats_data
        })

    @action(detail=True, methods=["get"], permission_classes=[IsAdminUser], url_path='client')
    def client_detail(self, request, pk=None):
        """Get detailed client information with activity history"""
        try:
            # Get client with activity statistics
            client = Client.objects.annotate(
                booking_count=Count('bookings', distinct=True),
                total_bookings_amount=Sum('bookings__total_amount'),
                total_paid_amount=Sum('bookings__total_amount', 
                                    filter=models.Q(bookings__payment_status='paid')),
                last_booking_date=Max('bookings__booking_date'),
                first_booking_date=models.Min('bookings__booking_date')
            ).select_related().get(id=pk)
            
            serializer = ClientDetailSerializer(client)
            
            return Response({
                'success': True,
                'message': 'Client details retrieved successfully',
                'client': serializer.data
            })
            
        except Client.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Client not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving client details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClientFilter(django_filters.FilterSet):
    """Filter for client list"""
    name = django_filters.CharFilter(method='filter_name')
    phone = django_filters.CharFilter(field_name='phone_number', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    region = django_filters.ChoiceFilter(field_name='region')
    city = django_filters.CharFilter(field_name='city_town', lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    is_verified = django_filters.BooleanFilter()
    has_bookings = django_filters.BooleanFilter(method='filter_has_bookings')
    joined_from = django_filters.DateFilter(field_name='date_joined__date', lookup_expr='gte')
    joined_to = django_filters.DateFilter(field_name='date_joined__date', lookup_expr='lte')
    
    class Meta:
        model = Client
        fields = ['gender', 'is_active', 'is_verified']
    
    def filter_name(self, queryset, name, value):
        """Filter by first name, last name, or other names"""
        return queryset.filter(
            models.Q(first_name__icontains=value) |
            models.Q(last_name__icontains=value) |
            models.Q(other_names__icontains=value)
        )
    
    def filter_has_bookings(self, queryset, name, value):
        """Filter clients with or without bookings"""
        if value:
            return queryset.filter(booking_count__gt=0)
        else:
            return queryset.filter(booking_count=0)


class ClientAuthViewSet(viewsets.GenericViewSet):

    def get_serializer_class(self):
        if self.action == "register":
            return ClientRegistrationSerializer
        elif self.action == "login":
            return ClientLoginSerializer
        elif self.action in ["profile", "update_profile"]:
            return ClientSerializer
        return None

    def get_permissions(self):
        if self.action in ["register", "login"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = ClientRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save()

            refresh = RefreshToken()
            refresh["client_id"] = str(client.id)
            refresh["user_type"] = "client"

            return Response(
                {
                    "success": True,
                    "message": AuthMessage.SUCCESS_REGISTER.value,
                    "user_type": "client",
                    "client_id": str(client.id),
                    "phone_number": client.get_masked_phone(),
                    "verification_required": True,
                }
            )
        return Response(
            {
                "success": False,
                "message": AuthMessage.REGISTRATION_FAILED.value,
                "errors": serializer.errors,
            }
        )

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = ClientLoginSerializer(data=request.data)
        if serializer.is_valid():
            client = serializer.validated_data["client"]
            client.last_login = timezone.now()
            client.save()

            refresh = RefreshToken()
            refresh["client_id"] = str(client.id)
            refresh["user_type"] = "client"

            return Response(
                {
                    "success": True,
                    "message": AuthMessage.SUCCESS_LOGIN.value,
                    "user_type": "client",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "client": ClientSerializer(client).data,
                }
            )
        return Response(
            {
                "success": False,
                "message": AuthMessage.ERROR_INVALID_CREDENTIALS.value,
                "errors": serializer.errors,
            }
        )

    @action(detail=False, methods=["post"])
    def verify_phone(self, request):
        client_id = request.data.get("client_id")
        otp = request.data.get("otp")

        if not client_id:
            return Response(
                {"success": False, "message": AuthMessage.CLIENT_NOT_FOUND.value}
            )

        if not otp:
            return Response(
                {"success": False, "message": AuthMessage.INVALID_OTP.value}
            )

        try:
            client = Client.objects.get(id=client_id)
            if otp == "1234":
                client.is_verified = True
                client.phone_verified_at = timezone.now()
                client.save()

                return Response(
                    {
                        "success": True,
                        "message": AuthMessage.SUCCESS_PHONE_VERIFIED.value,
                    }
                )
            else:
                return Response(
                    {"success": False, "message": AuthMessage.INVALID_OTP.value}
                )
        except Client.DoesNotExist:
            return Response(
                {"success": False, "message": AuthMessage.CLIENT_NOT_FOUND.value}
            )


class CustomTokenRefreshView(APIView):
    """
    Custom token refresh view that handles both admin users and clients
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            user_type = token.get('user_type')
            
            if user_type == 'client':
                # Handle client token refresh
                client_id = token.get('client_id')
                if not client_id:
                    return Response({
                        'success': False,
                        'message': 'Invalid client token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    client = Client.objects.get(id=client_id, is_active=True)
                    
                    # Create new refresh token for client
                    new_refresh = RefreshToken()
                    new_refresh['client_id'] = str(client.id)
                    new_refresh['user_type'] = 'client'
                    
                    # Blacklist old token if rotation is enabled
                    if hasattr(token, 'blacklist'):
                        token.blacklist()
                    
                    return Response({
                        'success': True,
                        'message': 'Token refreshed successfully',
                        'access': str(new_refresh.access_token),
                        'refresh': str(new_refresh),
                        'user_type': 'client'
                    })
                    
                except Client.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Client not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                    
            elif user_type == 'admin':
                # Handle admin token refresh
                user_id = token.get('user_id')
                if not user_id:
                    return Response({
                        'success': False,
                        'message': 'Invalid admin token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    user = User.objects.get(id=user_id, is_active=True)
                    
                    # Create new refresh token for admin
                    new_refresh = RefreshToken.for_user(user)
                    new_refresh['user_type'] = 'admin'
                    
                    # Blacklist old token if rotation is enabled
                    if hasattr(token, 'blacklist'):
                        token.blacklist()
                    
                    return Response({
                        'success': True,
                        'message': 'Token refreshed successfully',
                        'access': str(new_refresh.access_token),
                        'refresh': str(new_refresh),
                        'user_type': 'admin'
                    })
                    
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Handle standard JWT token (fallback)
                new_refresh = RefreshToken(refresh_token)
                
                return Response({
                    'success': True,
                    'message': 'Token refreshed successfully',
                    'access': str(new_refresh.access_token),
                    'refresh': str(new_refresh)
                })
                
        except TokenError as e:
            return Response({
                'success': False,
                'message': f'Token error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {
                        "success": False,
                        "message": AuthMessage.REFRESH_TOKEN_REQUIRED.value,
                    }
                )

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"success": True, "message": AuthMessage.SUCCESS_LOGOUT.value}
            )
        except Exception:
            return Response(
                {"success": False, "message": AuthMessage.INVALID_TOKEN.value}
            )

    @action(detail=False, methods=["get"])
    def profile(self, request):
        try:
            client_id = getattr(request.user, "id", None)
            if not client_id:
                return Response(
                    {"success": False, "message": AuthMessage.ERROR_UNAUTHORIZED.value}
                )

            client = Client.objects.get(id=client_id, is_active=True)
            serializer = ClientSerializer(client)

            return Response(
                {
                    "success": True,
                    "message": AuthMessage.SUCCESS_PROFILE_RETRIEVED.value,
                    "client": serializer.data,
                }
            )
        except Client.DoesNotExist:
            return Response(
                {"success": False, "message": AuthMessage.CLIENT_NOT_FOUND.value}
            )


class CustomTokenRefreshView(APIView):
    """
    Custom token refresh view that handles both admin users and clients
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            user_type = token.get('user_type')
            
            if user_type == 'client':
                # Handle client token refresh
                client_id = token.get('client_id')
                if not client_id:
                    return Response({
                        'success': False,
                        'message': 'Invalid client token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    client = Client.objects.get(id=client_id, is_active=True)
                    
                    # Create new refresh token for client
                    new_refresh = RefreshToken()
                    new_refresh['client_id'] = str(client.id)
                    new_refresh['user_type'] = 'client'
                    
                    # Blacklist old token if rotation is enabled
                    if hasattr(token, 'blacklist'):
                        token.blacklist()
                    
                    return Response({
                        'success': True,
                        'message': 'Token refreshed successfully',
                        'access': str(new_refresh.access_token),
                        'refresh': str(new_refresh),
                        'user_type': 'client'
                    })
                    
                except Client.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Client not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                    
            elif user_type == 'admin':
                # Handle admin token refresh
                user_id = token.get('user_id')
                if not user_id:
                    return Response({
                        'success': False,
                        'message': 'Invalid admin token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    user = User.objects.get(id=user_id, is_active=True)
                    
                    # Create new refresh token for admin
                    new_refresh = RefreshToken.for_user(user)
                    new_refresh['user_type'] = 'admin'
                    
                    # Blacklist old token if rotation is enabled
                    if hasattr(token, 'blacklist'):
                        token.blacklist()
                    
                    return Response({
                        'success': True,
                        'message': 'Token refreshed successfully',
                        'access': str(new_refresh.access_token),
                        'refresh': str(new_refresh),
                        'user_type': 'admin'
                    })
                    
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Handle standard JWT token (fallback)
                new_refresh = RefreshToken(refresh_token)
                
                return Response({
                    'success': True,
                    'message': 'Token refreshed successfully',
                    'access': str(new_refresh.access_token),
                    'refresh': str(new_refresh)
                })
                
        except TokenError as e:
            return Response({
                'success': False,
                'message': f'Token error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["put", "patch"])
    def update_profile(self, request):
        try:
            client_id = getattr(request.user, "id", None)
            if not client_id:
                return Response(
                    {"success": False, "message": AuthMessage.ERROR_UNAUTHORIZED.value}
                )

            client = Client.objects.get(id=client_id, is_active=True)
            serializer = ClientUpdateSerializer(
                client, data=request.data, partial=request.method == "PATCH"
            )

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "success": True,
                        "message": AuthMessage.SUCCESS_PROFILE_UPDATE.value,
                        "client": ClientSerializer(client).data,
                    }
                )
            else:
                return Response(
                    {
                        "success": False,
                        "message": AuthMessage.PROFILE_UPDATE_FAILED.value,
                        "errors": serializer.errors,
                    }
                )
        except Client.DoesNotExist:
            return Response(
                {"success": False, "message": AuthMessage.CLIENT_NOT_FOUND.value}
            )


class CustomTokenRefreshView(APIView):
    """
    Custom token refresh view that handles both admin users and clients
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            user_type = token.get('user_type')
            
            if user_type == 'client':
                # Handle client token refresh
                client_id = token.get('client_id')
                if not client_id:
                    return Response({
                        'success': False,
                        'message': 'Invalid client token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    client = Client.objects.get(id=client_id, is_active=True)
                    
                    # Create new refresh token for client
                    new_refresh = RefreshToken()
                    new_refresh['client_id'] = str(client.id)
                    new_refresh['user_type'] = 'client'
                    
                    # Blacklist old token if rotation is enabled
                    if hasattr(token, 'blacklist'):
                        token.blacklist()
                    
                    return Response({
                        'success': True,
                        'message': 'Token refreshed successfully',
                        'access': str(new_refresh.access_token),
                        'refresh': str(new_refresh),
                        'user_type': 'client'
                    })
                    
                except Client.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Client not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                    
            elif user_type == 'admin':
                # Handle admin token refresh
                user_id = token.get('user_id')
                if not user_id:
                    return Response({
                        'success': False,
                        'message': 'Invalid admin token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    user = User.objects.get(id=user_id, is_active=True)
                    
                    # Create new refresh token for admin
                    new_refresh = RefreshToken.for_user(user)
                    new_refresh['user_type'] = 'admin'
                    
                    # Blacklist old token if rotation is enabled
                    if hasattr(token, 'blacklist'):
                        token.blacklist()
                    
                    return Response({
                        'success': True,
                        'message': 'Token refreshed successfully',
                        'access': str(new_refresh.access_token),
                        'refresh': str(new_refresh),
                        'user_type': 'admin'
                    })
                    
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Handle standard JWT token (fallback)
                new_refresh = RefreshToken(refresh_token)
                
                return Response({
                    'success': True,
                    'message': 'Token refreshed successfully',
                    'access': str(new_refresh.access_token),
                    'refresh': str(new_refresh)
                })
                
        except TokenError as e:
            return Response({
                'success': False,
                'message': f'Token error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
