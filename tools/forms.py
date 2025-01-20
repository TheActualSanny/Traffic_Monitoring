import re
from django import forms

class MacForm(forms.Form):
    ''' This will have the necessary fields for inserting and/or deleting target MAC addresses '''
    target_mac = forms.CharField()

    def clean(self):
        '''
            Overridden clean method, checks if the given MAC address
            has the correct format for packet sniffing. 
        '''
        
        cleaned_data = super().clean()
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        if not mac_pattern.match(cleaned_data.get('target_mac')):
            raise forms.ValidationError('The MAC address must have a valid format!')
        else:
            return cleaned_data
        
class SnifferForm(forms.Form):
    '''
        The user will set up the sniffer config here.
    '''
    network_interface = forms.CharField()
    packet_limit = forms.IntegerField(min_value = 1)
    traffic_directory = forms.CharField(max_length = 40, required = False,
                                        widget = forms.TextInput(attrs = {'disabled' : 'disabled'}))
    save_locally = forms.BooleanField(required = False)
    