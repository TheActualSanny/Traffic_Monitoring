import redis
import requests
from .tasks import send_key
from .forms import EmailForm
from django.views import View
from django.contrib import messages
from rest_framework.views import APIView
from .serializers import LookupSerializer
from lookup_interface.models import LookupInstances
from lookup_interface.lookups.main import target_lookup
from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.permissions import HasAPIKey

class KeyView(View):
    '''
        This view will handle the logic for sending
        the API Key to the user via email.
    '''
    def get(self, request):
        email_form = EmailForm()
        return render(request, 'lookups_api/api_key.html', context = {'email_form' : email_form})

    def post(self, request):
        email_form = EmailForm(request.POST)
        if email_form.is_valid():
            email_address = email_form.cleaned_data[0].get('email_address')
            api_key, key = APIKey.objects.create_key(name = email_address)
            send_key.delay(key, email_address)
            messages.success(request, message = 'API Key sent successfully sent!')
            return redirect('lookups_api:send_key')

class LookupAPI(APIView):

    permission_classes = [HasAPIKey]

    def get(self, request):
        lookups = LookupInstances.objects.all()
        serializer = LookupSerializer(data = lookups)
        serializer.is_valid()
        return Response(serializer.data)

    def post(self, request):
        '''
            Does the same exact thing that the user can do using
            the web interface, though, this time the response will be in JSON format.
        '''
        data = LookupInstances.objects.all()
        if data:
            data.delete()
        target = request.data.get('target')
        manager = target_lookup(target = target, api = True)
        serializer = LookupSerializer(data = data, many = True)
        serializer.is_valid()
        return Response(serializer.data)

