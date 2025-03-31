from django.db import models

# Create your models here.
class IpLookups(models.Model):
    id = models.IntegerField(primary_key = True)
    status = models.CharField(max_length = 10)
    ip_address = models.CharField(max_length = 15)
    langitude = models.FloatField(null = True)
    longitude = models.FloatField(null = True)
    location = models.CharField(max_length = 20, null = True)
    isp = models.CharField(max_length = 100, null = True)

