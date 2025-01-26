import json
from scapy.all import get_if_list
from .traffic.main import start_sniffing
from .lookups.main import target_lookup
from .forms import MacForm, SnifferForm
from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import TargetInstances, PacketInstances, LookupInstances

# These will probably be written as attributes
# Instead of function_called, I can directly check the shutdown_event to see if its set or not.
function_called = False
main_sniffer = None
lookup_manager = None
data_fetched = False

def invoke_sniffer(request):
    '''
        View responsible for calling the start_sniffing function.
        For now, user can only set necessary params for the sniffing to proceed.
        However, there will also be a way to stop the sniffing process to re-configure the params.
    '''
    global main_sniffer, function_called

    if request.method == 'POST':
        sniffer_form = SnifferForm(request.POST)
        if sniffer_form.is_valid():
            packet_limit = sniffer_form.cleaned_data.get('packet_limit')
            interface = sniffer_form.cleaned_data.get('network_interface')
            local_storage = sniffer_form.cleaned_data.get('save_locally')
            traffic_dir = sniffer_form.cleaned_data.get('traffic_directory')
            print(traffic_dir)
            if not function_called and not main_sniffer:
                main_sniffer = start_sniffing(packet_limit = packet_limit, network_interface = interface,
                                              initial_dir = traffic_dir, local_storage = local_storage)
                function_called = True
                messages.success(request, message = 'Successfully started the sniffer!')
            elif main_sniffer:
                function_called = True
                main_sniffer.packets_per_file = packet_limit
                main_sniffer.target_manager.macs.clear()
                main_sniffer.shutdown_event.clear()
                if local_storage:
                    main_sniffer.target_manager.update_dir(traffic_dir)
                main_sniffer.start(interface)
                messages.success(request, message = 'Successfully started the sniffer!')
            else:
                messages.debug(request, message = 'Sniffer was already started.')
    return redirect('tools:add-mac')
    
def terminate_sniffer(request):
    '''
        This view will be called whenever the user pauses the sniffer in order to change the configuration or
        fetch the finalized pcap data
    '''
    global function_called
    
    if request.method == 'POST':
        if function_called:
            function_called = False
            main_sniffer.shutdown_handler()
            main_sniffer.available_macs.clear()
            TargetInstances.objects.all().delete()
            messages.success(request, message = 'Successfully terminated the sniffer!')
        else:
            messages.error(request, message = "The sniffer isn't started yet.")
    return redirect('tools:add-mac')

def add_mac(request):
    '''
        View responsible for adding a target MAC address.
        Calls the clean method on MacForm() and checks if the passed MAC has the right format.
        If it does, for not, it only loads a success message, but it will write it to our target database.
    '''
    if not request.session.get('last_index'):
        request.session['last_index'] = 0

    if not main_sniffer and not function_called:
        TargetInstances.objects.all().delete()
    added_targets = TargetInstances.objects.all()
    if request.method == 'POST':
        mac_form = MacForm(request.POST)
        if mac_form.is_valid():
            if main_sniffer and not main_sniffer.shutdown_event.is_set():
                mac_address = mac_form.cleaned_data.get('target_mac')
                main_sniffer.target_manager.add_target(mac_address)
                TargetInstances.objects.create(mac_address = mac_address)
                messages.success(request, message = 'Successfully added a target MAC!')
            else:
                messages.error(request, message = 'Start the sniffer before you add a target.')
            
    else:
        mac_form = MacForm()
    return render(request, 'tools/traffic_monitor.html', context = {'macform' : mac_form, 'targets' : added_targets, 
                                                                    'snform' : SnifferForm()})

def remove_target(request):
    '''
        Once the 'Remove Target' button is clicked, this view is called. It removes that 
        target from the TargetInstances table and redirects to the initial page
    '''
    if request.method == 'POST':
        dynamic_request = False
        try:
            address = json.loads(request.body).get('address')
            dynamic_request = True
        except:
            address = request.POST.get('address')
        TargetInstances.objects.filter(mac_address = address).delete()
        main_sniffer.target_manager.delete_target(address)
        if dynamic_request:
            return JsonResponse({'success' : True})
    return redirect('tools:add-mac')

def lookup_page(request):
    '''
        This will be the main view for the lookups. A seperate method will be made in order to initiate the searching
    '''
    if not request.session.get('lookup_last_index'):
            request.session['lookup_last_index'] = 0
    lookups = LookupInstances.objects.all()
    if lookups:
        lookups.delete()
    return render(request, 'tools/name_lookups.html', context = {})

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
            if not lookup_manager:
                lookup_manager = target_lookup(target)
            else:
                lookup_manager.main_lookup(target)
            messages.success(request, message = 'Started searching...')
        else:
            messages.error(request, message = 'Input a target username!')
    return redirect('tools:lookups')

# TODO: Automatically fetch current user's interface.
def get_networkifc(request) -> JsonResponse:
    '''
        This will be a URL to which the Front-end will send a GET request
        so that the user can auto-fill the network interface field.

        Considering that the first interface name in the list is usually 'lo', we get the second element.
    '''
    if request.method == 'GET':
        interface = get_if_list() 
        return JsonResponse({'interfaces' : interface})
    
def get_packets(request) -> JsonResponse:
    '''
        The Front-end will make a call to this url to update the packets container dynamically every couple
        of seconds
    '''
    global main_sniffer

    if request.method == 'GET':
        first = None
        if main_sniffer and not main_sniffer.packet_caught:
            potential = PacketInstances.objects.all()
            if potential:
                id = potential.first().id
                request.session['last_index'] = id
                first = id
                main_sniffer.packet_caught = True
        last_index = request.session['last_index']

        if last_index:
            packets = list()
            if first == last_index:
                packets.append(potential.values()[0])
            new_packets = list(PacketInstances.objects.filter(id__gt = last_index).values())
            packets.extend(new_packets)
            request.session['last_index'] += len(new_packets)
            if packets:
                for packet in packets:
                    packet.pop('packet_data')
                print(packets)
                return JsonResponse({'packets' : packets})
        
        return JsonResponse({'packets' : None})
    

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
                    if record.get('profile_pic_url'):
                        finalized_data.append({record.get('profile_url') : 'Account found!'})   
                    else:
                        finalized_data.append({record.get('profile_url') : 'Account either private or it doesnt exist'})
                print(finalized_data)
                return JsonResponse({'data' : finalized_data})     
        return JsonResponse({'data' : None})  
    

def get_macs(request):
    '''
        The Front-end will make requests to this every couple of seconds in order to add the macs 
        on the website
    '''
    if request.method == 'GET':
        if main_sniffer:
            return JsonResponse({'entries' : main_sniffer.available_macs})
        return JsonResponse({'' : None})


def manage_target(request):
    '''
        This method will be called everytime the user selects a new target within the list of MACs.
        It is necessary to update the available_macs dict in order for the Front-end to
        color the button if it was checked.
    '''
    global main_sniffer

    if request.method == 'POST':
        request_data = json.loads(request.body)
        mac = request_data.get('mac_address')
        new_status = request_data.get('selected')

        for entry in main_sniffer.available_macs:
            if entry.get('mac') == mac:
                if new_status:
                    TargetInstances.objects.create(mac_address = mac)
                    main_sniffer.target_manager.add_target(mac)
                    entry['selected'] = True
                else:
                    TargetInstances.objects.filter(mac_address = mac).delete()
                    main_sniffer.target_manager.delete_target(mac)
                    entry['selected'] = False

        print(main_sniffer.available_macs)
        return HttpResponse('')
