from configparser import ConfigParser

class Config:
    def __init__(self, config_path="config.ini"):
        self.config = ConfigParser()
        self.config.read(config_path)

    def get_server_settings(self):
        return (
            self.config.getint("ServerSettings", "SERVER_PORT"),
            self.config.getint("ServerSettings", "BUFFER_SIZE"),
            self.config.get("ServerSettings", "INTERFACE")
        )

    def get_file_directory_settings(self):
        return self.config.get("FileDirectorySettings", "NETWORK_RANGE")

    def get_broadcast_settings(self):
        return self.config.get("BroadcastSettings", "BROADCAST_MAC")

    def get_packet_handling_settings(self):
        return self.config.get("PacketHandlingSettings", "PACKETS_PER_FILE")

    def get_google_cloud_storage_settings(self):
        return (
            self.config.get("GoogleCloudStorageSettings", "BUCKET_NAME"),
            self.config.get("FileDirectorySettings", "CREDENTIAL_PATH")
        )

config = Config()
