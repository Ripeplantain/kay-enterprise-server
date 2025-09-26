from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from .models import BusQuote
from .serializers import BusQuoteRequestSerializer, BusQuoteResponseSerializer


class BusQuoteThrottle(AnonRateThrottle):
    rate = '10/hour'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([BusQuoteThrottle])
def request_bus_quote(request):
    serializer = BusQuoteRequestSerializer(data=request.data)

    if serializer.is_valid():
        try:
            quote = serializer.save()

            send_customer_confirmation_email(quote)
            send_admin_notification_email(quote)

            response_data = BusQuoteResponseSerializer(quote).data

            return Response({
                'success': True,
                'message': 'Quote request submitted successfully',
                'data': response_data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to submit quote request. Please try again.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'success': False,
        'message': 'Validation failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


def send_customer_confirmation_email(quote):
    print(f"[MOCK EMAIL] Customer confirmation sent to {quote.email}")
    print(f"Subject: KayExpress Bus Rental Quote Request Received")
    print(f"Reference: {quote.reference_number}")
    print(f"Trip: {quote.pickup_location} to {quote.destination}")


def send_admin_notification_email(quote):
    print(f"[MOCK EMAIL] Admin notification for quote {quote.reference_number}")
    print(f"Customer: {quote.full_name} ({quote.phone_number})")
    print(f"Trip: {quote.pickup_location} to {quote.destination} on {quote.travel_date}")
    print(f"Passengers: {quote.passengers}")
