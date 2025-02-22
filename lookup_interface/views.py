import json
from .models import LookupInstances
from django.core.cache import cache
from django.contrib import messages
from .lookups.main import target_lookup
from .handle_cache import convert_cache
from django.http import JsonResponse
from django.shortcuts import render, redirect

lookup_manager = None

def lookup_page(request):
    '''
        This will be the main view for the lookups. A seperate method will be made in order to initiate the searching
    '''

    lookups = LookupInstances.objects.all()
    if lookups:
        lookups.delete()
    cached = request.session.get('cached_target')
    context = {}
    if cached:
        request.session.pop('cached_target')
        context = {'cached_data' : convert_cache(cached)}

    return render(request, 'lookup_interface/name_lookups.html', context = context)

def initiate_lookups(request):
    '''
        Starts searching for accounts.
        We also set a session variable here in order to load the new records correctly.
    '''
    global lookup_manager
    
    if request.method == 'POST':
        target = request.POST.get('target')
        lookups = LookupInstances.objects.all()
        if lookups:
            lookups.delete()
        if target:
            if cache.get(target):
                request.session['cached_target'] = json.loads(cache.get(target)) 
            else:
                cache.set(target, [], timeout = 300)
                if not lookup_manager:
                    lookup_manager = target_lookup(target, api = False)
                else:
                    lookup_manager.main_lookup(target, api = False)
                messages.success(request, message = 'Started searching...') 
        else:
            messages.error(request, message = 'Input a target username!')
    return redirect('lookup_interface:lookups')