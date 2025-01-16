from scapy.all import get_if_list
from .traffic.main import start_sniffing
from .forms import MacForm, SnifferForm
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import TargetInstances, PacketInstances

# These will probably be written as attributes
# Instead of function_called, I can directly check the shutdown_event to see if its set or not.
function_called = False
main_sniffer = None


def invoke_sniffer(request):
    '''
        View responsible for calling the start_sniffing function.
        For now, user can only set necessary params for the sniffing to proceed.
        However, there will also be a way to stop the sniffing process to re-configure the params.
    '''
    global main_sniffer
    global function_called

    if request.method == 'POST':
        sniffer_form = SnifferForm(request.POST)
        if sniffer_form.is_valid():
            packet_limit = sniffer_form.cleaned_data.get('packet_limit')
            interface = sniffer_form.cleaned_data.get('network_interface')
            traffic_dir = sniffer_form.cleaned_data.get('traffic_directory')
            if not function_called and not main_sniffer:
                main_sniffer = start_sniffing(packet_limit = packet_limit, network_interface = interface,
                                              initial_dir = traffic_dir)
                function_called = True
                messages.success(request, message = 'Successfully started the sniffer!')
            elif main_sniffer:
                function_called = True
                main_sniffer.packets_per_file = packet_limit
                main_sniffer.target_manager.macs.clear()
                main_sniffer.shutdown_event.clear()
                # main_sniffer.target_manager.update_dir(traffic_dir)
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
    if not main_sniffer and not function_called:
        TargetInstances.objects.all().delete()
    added_targets = TargetInstances.objects.all()
    if request.method == 'POST':
        mac_form = MacForm(request.POST)
        if mac_form.is_valid():
            try:
                mac_address = mac_form.cleaned_data.get('target_mac')
                main_sniffer.target_manager.add_target(mac_address)
                TargetInstances.objects.create(mac_address = mac_address)
                messages.success(request, message = 'Successfully added a target MAC!')
            except:
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
        address = request.POST.get('address')
        TargetInstances.objects.filter(mac_address = address).delete()
        main_sniffer.target_manager.delete_target(address)
    return redirect('tools:add-mac')


def get_networkifc(request) -> JsonResponse:
    '''
        This will be a URL to which the Front-end will send a GET request
        so that the user can auto-fill the network interface field.

        Considering that the first interface name in the list is usually 'lo', we get the second element.
    '''
    if request.method == 'GET':
        interface = get_if_list()[1] 
        return JsonResponse({'interface_name' : interface})
    
def get_packets(request) -> JsonResponse:
    '''
        The Front-end will make a call to this url to update the packets container dynamically every couple
        of seconds
    '''
    if request.method == 'GET':
        packets = list(PacketInstances.objects.all().values())
        for packet in packets:
            packet.pop('packet_data')
        print(packets)
        if packets:
            return JsonResponse({'packets' : packets})
        else:
            return JsonResponse({'packets' : None})