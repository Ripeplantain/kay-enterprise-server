from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.authentication import get_authorization_header
from rest_framework.permissions import BasePermission
from django.contrib.auth.models import User
from .models import Client

class ClientJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication for clients"""
    
    def authenticate(self, request):
        header = get_authorization_header(request).split()
        
        if not header or header[0].lower() != b'bearer':
            return None
            
        if len(header) != 2:
            return None
            
        try:
            token = header[1].decode('utf-8')
            validated_token = self.get_validated_token(token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except (InvalidToken, TokenError, UnicodeDecodeError):
            return None
    
    def get_user(self, validated_token):
        try:
            client_id = validated_token.get('client_id')
            user_type = validated_token.get('user_type')
            
            if user_type == 'client' and client_id:
                client = Client.objects.get(id=client_id, is_active=True)
                return client
            elif user_type == 'admin':
                user_id = validated_token.get('user_id')
                return User.objects.get(id=user_id, is_active=True)
        except (Client.DoesNotExist, User.DoesNotExist):
            raise InvalidToken('User not found')
        
        raise InvalidToken('Invalid token type')

class ClientPermission(BasePermission):
    """Custom permission class for client endpoints"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            hasattr(request.user, 'phone_number') and
            request.user.is_active
        )


class ClientOrAdminPermission(BasePermission):
    """Custom permission class that allows both clients and admins"""
    
    def has_permission(self, request, view):
        if not request.user:
            return False
        
        # Check if it's an authenticated admin (Django User)
        if hasattr(request.user, 'is_staff') and request.user.is_authenticated:
            return True
        
        # Check if it's an authenticated client
        if hasattr(request.user, 'phone_number') and hasattr(request.user, 'is_active'):
            return request.user.is_active
        
        return False
