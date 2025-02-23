import re
from django import forms


class EmailForm(forms.Form):
    email_address = forms.CharField()

    def clean(self):
        '''
            Checks if the structure of the passed email address is valid.
        '''
        super().clean()
        address = self.cleaned_data.get('email_address')
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return (self.cleaned_data, bool(email_pattern.match(address)))