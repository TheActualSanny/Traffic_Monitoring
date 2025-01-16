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

class PacketInstances(models.Model):
    '''
        Table for storing packet instances that are fetched by the sniffer.
        These will also be written in a seperate pcap file if the user needs it in that format.
        Also, the implementation of this will change later on
    '''
    corresponding_target = models.ForeignKey(TargetInstances, on_delete = models.CASCADE, null = True)
    dst_mac = models.CharField(max_length = 17)
    src_ip = models.CharField(max_length = 40)
    dst_ip = models.CharField(max_length = 40)
    packet_data = models.BinaryField(max_length = 1024)
