import json
from scapy.all import get_if_list
from .traffic.main import start_sniffing
from .forms import MacForm, SnifferForm
from django.core.cache import cache
from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TargetInstances, PacketInstances

class TrafficMonitoring:

    function_called = False
    main_sniffer = None
  
    @staticmethod
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
                # TODO: Add options to store pcaps in different databases
                local_storage = sniffer_form.cleaned_data.get('save_locally')
                traffic_dir = sniffer_form.cleaned_data.get('traffic_directory')
                kafka_topic = sniffer_form.cleaned_data.get('kafka_topic')
                kafka_broker = sniffer_form.cleaned_data.get('kafka_broker')
                kafka_group_id = sniffer_form.cleaned_data.get('kafka_group_id')
                kafka_directory = sniffer_form.cleaned_data.get('kafka_directory')

                if not TrafficMonitoring.function_called and not TrafficMonitoring.main_sniffer:
                    TrafficMonitoring.main_sniffer = start_sniffing(packet_limit = packet_limit, network_interface = interface,
                                                initial_dir = traffic_dir, local_storage = local_storage,
                                                initial_broker = kafka_broker, initial_topic = kafka_topic,
                                                initial_group_id = kafka_group_id, initial_directory = kafka_directory)
                    TrafficMonitoring.function_called = True
                    messages.success(request, message = 'Successfully started the sniffer!')
                elif main_sniffer:
                    function_called = True
                    TrafficMonitoring.main_sniffer.packets_per_file = packet_limit
                    TrafficMonitoring.main_sniffer.target_manager.macs.clear()
                    TrafficMonitoring.main_sniffer.shutdown_event.clear()
                    if local_storage:
                        TrafficMonitoring.main_sniffer.target_manager.update_dir(traffic_dir)
                    TrafficMonitoring.main_sniffer.update_kafka(new_broker = kafka_broker, new_topic = kafka_topic,
                                            new_group_id = kafka_group_id, new_kafka_directory = kafka_directory)
                    TrafficMonitoring.main_sniffer.start(interface)
                    messages.success(request, message = 'Successfully started the sniffer!')
                else:
                    messages.debug(request, message = 'Sniffer was already started.')
        return redirect('tools:add-mac')
        
    @staticmethod
    def terminate_sniffer(request):
        '''
            This view will be called whenever the user pauses the sniffer in order to change the configuration or
            fetch the finalized pcap data
        '''

        if request.method == 'POST':
            if TrafficMonitoring.function_called:
                TrafficMonitoring.function_called = False
                TrafficMonitoring.main_sniffer.shutdown_handler()
                TrafficMonitoring.main_sniffer.available_macs.clear()
                TargetInstances.objects.all().delete()
                messages.success(request, message = 'Successfully terminated the sniffer!')
            else:
                messages.error(request, message = "The sniffer isn't started yet.")
        return redirect('tools:add-mac')

    @staticmethod
    def add_mac(request):
        '''
            View responsible for adding a target MAC address.
            Calls the clean method on MacForm() and checks if the passed MAC has the right format.
            If it does, for not, it only loads a success message, but it will write it to our target database.
        '''
        if not request.session.get('last_index'):
            request.session['last_index'] = 0

        if not TrafficMonitoring.main_sniffer and not TrafficMonitoring.function_called:
            TargetInstances.objects.all().delete()
        added_targets = TargetInstances.objects.all()
        if request.method == 'POST':
            mac_form = MacForm(request.POST)
            if mac_form.is_valid():
                if TrafficMonitoring.main_sniffer and not TrafficMonitoring.main_sniffer.shutdown_event.is_set():
                    mac_address = mac_form.cleaned_data.get('target_mac')
                    TrafficMonitoring.main_sniffer.target_manager.add_target(mac_address)
                    TargetInstances.objects.create(mac_address = mac_address)
                    messages.success(request, message = 'Successfully added a target MAC!')
                else:
                    messages.error(request, message = 'Start the sniffer before you add a target.')
                
        else:
            mac_form = MacForm()
        return render(request, 'tools/traffic_monitor.html', context = {'macform' : mac_form, 'targets' : added_targets, 
                                                                        'snform' : SnifferForm()})

    @staticmethod
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
            TrafficMonitoring.main_sniffer.target_manager.delete_target(address)
            if dynamic_request:
                return JsonResponse({'success' : True})
        return redirect('tools:add-mac')

    @staticmethod
    def get_networkifc(request) -> JsonResponse:
        '''
            This will be a URL to which the Front-end will send a GET request
            so that the user can auto-fill the network interface field.

            Considering that the first interface name in the list is usually 'lo', we get the second element.
        '''
        if request.method == 'GET':
            interface = get_if_list() 
            return JsonResponse({'interfaces' : interface})
        
        
    @staticmethod
    def get_macs(request):
        '''
            The Front-end will make requests to this every couple of seconds in order to add the macs 
            on the website
        '''
        if request.method == 'GET':
            if TrafficMonitoring.main_sniffer:
                available_macs = TrafficMonitoring.main_sniffer.fetch_macs()
                print(available_macs)
                return JsonResponse({'entries' : available_macs})
            else:
                return JsonResponse({'entries' : None})

    @staticmethod
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

            for entry in TrafficMonitoring.main_sniffer.available_macs:
                if entry.get('mac') == mac:
                    if new_status:
                        TargetInstances.objects.create(mac_address = mac)
                        TrafficMonitoring.main_sniffer.target_manager.add_target(mac)
                        entry['selected'] = True
                    else:
                        entry['selected'] = False
            return HttpResponse('')
