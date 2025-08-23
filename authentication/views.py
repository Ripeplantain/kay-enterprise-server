from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.utils import timezone

from utils.enums.auth import AuthMessage
from .models import Client
from .serializers import (
    AdminLoginSerializer, ClientRegistrationSerializer, ClientLoginSerializer,
    AdminSerializer, ClientSerializer, ClientUpdateSerializer
)

class AdminAuthViewSet(viewsets.GenericViewSet):
    """Admin authentication using Django User model"""
    
    def get_permissions(self):
        if self.action in ['login']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Admin login"""
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.last_login = timezone.now()
            user.save()
            
            refresh = RefreshToken.for_user(user)
            return Response({
                'success': True,
                'message': AuthMessage.SUCCESS_ADMIN_LOGIN.value,
                'user_type': 'admin',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': AdminSerializer(user).data
            })
        return Response({
            'success': False,
            'message': AuthMessage.ERROR_ADMIN_INVALID_CREDENTIALS.value,
            'errors': serializer.errors
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Admin logout"""
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    'success': False,
                    'message': AuthMessage.REFRESH_TOKEN_REQUIRED.value
                })
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'success': True,
                'message': AuthMessage.SUCCESS_ADMIN_LOGOUT.value
            })
        except Exception:
            return Response({
                'success': False,
                'message': AuthMessage.INVALID_TOKEN.value
            })

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get admin profile"""
        serializer = AdminSerializer(request.user)
        return Response({
            'success': True,
            'message': AuthMessage.SUCCESS_ADMIN_PROFILE.value,
            'user': serializer.data
        })

class ClientAuthViewSet(viewsets.GenericViewSet):
    """Client authentication using custom Client model"""
    
    def get_permissions(self):
        if self.action in ['register', 'login']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register new client"""
        serializer = ClientRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save()
            
            # Create JWT token for client (custom implementation needed)
            refresh = RefreshToken()
            refresh['client_id'] = str(client.id)
            refresh['user_type'] = 'client'
            
            return Response({
                'success': True,
                'message': AuthMessage.SUCCESS_REGISTER.value,
                'user_type': 'client',
                'client_id': str(client.id),
                'phone_number': client.get_masked_phone(),
                'verification_required': True
            })
        return Response({
            'success': False,
            'message': AuthMessage.REGISTRATION_FAILED.value,
            'errors': serializer.errors
        })

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Client login"""
        serializer = ClientLoginSerializer(data=request.data)
        if serializer.is_valid():
            client = serializer.validated_data['client']
            client.last_login = timezone.now()
            client.save()
            
            # Create custom JWT token for client
            refresh = RefreshToken()
            refresh['client_id'] = str(client.id)
            refresh['user_type'] = 'client'
            
            return Response({
                'success': True,
                'message': AuthMessage.SUCCESS_LOGIN.value,
                'user_type': 'client',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'client': ClientSerializer(client).data
            })
        return Response({
            'success': False,
            'message': AuthMessage.ERROR_INVALID_CREDENTIALS.value,
            'errors': serializer.errors
        })

    @action(detail=False, methods=['post'])
    def verify_phone(self, request):
        """Verify phone number with OTP"""
        client_id = request.data.get('client_id')
        otp = request.data.get('otp')
        
        if not client_id:
            return Response({
                'success': False,
                'message': AuthMessage.CLIENT_NOT_FOUND.value
            })
            
        if not otp:
            return Response({
                'success': False,
                'message': AuthMessage.INVALID_OTP.value
            })
        
        try:
            client = Client.objects.get(id=client_id)
            # In real implementation, verify OTP here
            if otp == '1234':  # Placeholder for demo
                client.is_verified = True
                client.phone_verified_at = timezone.now()
                client.save()
                
                return Response({
                    'success': True,
                    'message': AuthMessage.SUCCESS_PHONE_VERIFIED.value
                })
            else:
                return Response({
                    'success': False,
                    'message': AuthMessage.INVALID_OTP.value
                })
        except Client.DoesNotExist:
            return Response({
                'success': False,
                'message': AuthMessage.CLIENT_NOT_FOUND.value
            })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Client logout"""
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    'success': False,
                    'message': AuthMessage.REFRESH_TOKEN_REQUIRED.value
                })
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'success': True,
                'message': AuthMessage.SUCCESS_LOGOUT.value
            })
        except Exception:
            return Response({
                'success': False,
                'message': AuthMessage.INVALID_TOKEN.value
            })

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get client profile"""
        try:
            # Extract client_id from JWT token
            client_id = getattr(request.user, 'id', None)
            if not client_id:
                return Response({
                    'success': False,
                    'message': AuthMessage.ERROR_UNAUTHORIZED.value
                })
            
            client = Client.objects.get(id=client_id, is_active=True)
            serializer = ClientSerializer(client)
            
            return Response({
                'success': True,
                'message': AuthMessage.SUCCESS_PROFILE_RETRIEVED.value,
                'client': serializer.data
            })
        except Client.DoesNotExist:
            return Response({
                'success': False,
                'message': AuthMessage.CLIENT_NOT_FOUND.value
            })

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update client profile"""
        try:
            # Extract client_id from JWT token
            client_id = getattr(request.user, 'id', None)
            if not client_id:
                return Response({
                    'success': False,
                    'message': AuthMessage.ERROR_UNAUTHORIZED.value
                })
            
            client = Client.objects.get(id=client_id, is_active=True)
            serializer = ClientUpdateSerializer(
                client, 
                data=request.data, 
                partial=request.method == 'PATCH'
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': AuthMessage.SUCCESS_PROFILE_UPDATE.value,
                    'client': ClientSerializer(client).data
                })
            else:
                return Response({
                    'success': False,
                    'message': AuthMessage.PROFILE_UPDATE_FAILED.value,
                    'errors': serializer.errors
                })
        except Client.DoesNotExist:
            return Response({
                'success': False,
                'message': AuthMessage.CLIENT_NOT_FOUND.value
            })
