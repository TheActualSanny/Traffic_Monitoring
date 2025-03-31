import re
from rest_framework import serializers

class IpValidator(serializers.Serializer):
    address = serializers.CharField()

    def validate_address(self, value):
        '''
            This will be called to check that the passed Ip address is in a  valid IPv4 format
        '''
        pattern = r"""^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.
                    (25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.
                    (25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.
                    (25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"""
        
        if not bool(re.match(pattern, value)):
            raise serializers.ValidationError('Make sure that the passed address is in the right format!')
    