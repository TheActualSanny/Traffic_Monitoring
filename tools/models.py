from django.db import models
from django.contrib.auth.models import User

class TargetInstances(models.Model):
    '''
        Table for storing the target MAC addresses that the user stores.
        For now, it has 2 fields, though after I add user authentication, it will probably
        contain fields (or a many to one field) to a user instance.
    '''
    id = models.AutoField(primary_key = True)
    mac_address = models.CharField(max_length = 17)
