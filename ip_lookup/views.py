from .serializers import IpValidator
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

class IPLookup(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'message' : 'Pass a valid IP address to fetch data on the host!'})

    def post(self, request):
        passed_ip = request.data.get('ip')
        validator = IpValidator(data = request.data)       
        if validator.is_valid():
            pass 