from django.db import models

class LookupInstances(models.Model):
    '''
        Table for storing the lookup results' data. Even though different APIs are used for the data fetching,
        common fields are written here and the records are isnerted.
    '''
    id = models.AutoField(primary_key = True)
    username = models.CharField(max_length = 50)
    profile_pic_url = models.CharField(max_length = 1000, null = True)
    profile_url = models.CharField(max_length = 500, default = None)
    status = models.CharField(max_length = 50)