# from tools.models import LookupInstances
from rest_framework import serializers

class LookupSerializer(serializers.ModelSerializer):
    '''
        This will serialize all of the lookup instances
        in our model into JSON format.
    '''

    class Meta:
        # model = LookupInstances
        exclude = ('id',)