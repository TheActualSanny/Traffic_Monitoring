from .models import LookupInstances
from django.core.cache import cache
from django.contrib import messages
from .lookups.main import target_lookup
from .handle_cache import load_cache
from django.http import JsonResponse
from django.shortcuts import render, redirect

lookup_manager = None
data_fetched = False

def lookup_page(request):
    '''
        This will be the main view for the lookups. A seperate method will be made in order to initiate the searching
    '''
    if not request.session.get('lookup_last_index'):
            request.session['lookup_last_index'] = 0
    lookups = LookupInstances.objects.all()
    if lookups:
        lookups.delete()
    return render(request, 'lookup_interface/name_lookups.html', context = {})

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
            if not cache.get(target):
                cache.set(target, [], timeout = 300)
                if not lookup_manager:
                    lookup_manager = target_lookup(target, api = False)
                else:
                    lookup_manager.main_lookup(target, api = False)
                messages.success(request, message = 'Started searching...')
            else:
                lookup_records = load_cache(target)
                request.session[target] = lookup_records
        else:
            messages.error(request, message = 'Input a target username!')
    return redirect('lookup_interface:lookups')


def get_lookups(request) -> JsonResponse:
    '''
        The front-end sends a GET request to this view and we get latest found records regarding lookups. 
    '''
    global lookup_manager, data_fetched

    if request.method == 'GET':
        initial_index = None
        if lookup_manager and not data_fetched:
            potential_data = LookupInstances.objects.all()
            if potential_data:
                id = potential_data.first().id
                request.session['lookup_last_index'] = id
                initial_index = id
                data_fetched = True
        last_index = request.session['lookup_last_index']

        if last_index:
            fetched = list()
            if last_index == initial_index:
                fetched.append(potential_data.values()[0])
            new_data = list(LookupInstances.objects.filter(id__gt = last_index).values())
            fetched.extend(new_data)
            request.session['lookup_last_index'] += len(new_data)
            finalized_data = list()
            if fetched:
                for record in fetched:
                    finalized_data.append({record.get('profile_url') : record.get('status')})   
                return JsonResponse({'data' : finalized_data})     
        return JsonResponse({'data' : None})  