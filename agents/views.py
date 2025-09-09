from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from .models import Agent
from .serializers import AgentRegistrationSerializer, AgentResponseSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_agent(request):
    try:
        with transaction.atomic():
            serializer = AgentRegistrationSerializer(data=request.data)
            
            if serializer.is_valid():
                agent = serializer.save()
                response_data = AgentResponseSerializer(agent).data
                
                return Response({
                    "success": True,
                    "message": "Agent application submitted successfully",
                    "data": {
                        "agent_id": response_data['id'],
                        "reference_number": response_data['reference_number']
                    }
                }, status=status.HTTP_201_CREATED)
            
            else:
                return Response({
                    "success": False,
                    "message": "Validation failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        return Response({
            "success": False,
            "message": "An error occurred while processing your request",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
