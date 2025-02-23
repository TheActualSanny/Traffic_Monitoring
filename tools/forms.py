import re
from django import forms
from django.contrib.auth.models import User
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
    kafka_broker = forms.CharField()
    kafka_topic = forms.CharField()
    kafka_group_id = forms.CharField()
    kafka_directory = forms.CharField(required = False)

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget = forms.PasswordInput)
    password_confirm = forms.CharField(widget = forms.PasswordInput, label = 'Confirm Password')
    class Meta:
        model = User
        fields = ('username', 'password', 'password_confirm')
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Please input the correct password in the confirm field!')
        return cleaned_data