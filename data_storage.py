import os
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from config import MAX_WORKERS, BUCKET_NAME, CREDENTIAL_PATH, SOURCE_DESTINATION
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Event
import logging
from dataclasses import dataclass
import threading
import time

import logging
from traffic_logger import logger_setup

logger_setup()
logger = logging.getLogger(__name__)


@dataclass
class FileEventHandler(FileSystemEventHandler):
    """
    Handles file events and performs actions such as uploading files to a Google Cloud Storage bucket.

    Attributes:
        bucket (google.cloud.storage.Bucket): The Google Cloud Storage bucket to upload files to.
        source_destination (str): The source directory from which files are monitored.
        shutdown_event (threading.Event): Event to signal shutdown.

    Methods:
        on_created(event): Overrides the parent class method to handle file creation events.
        upload_file(local_file_path): Uploads a file to the specified Google Cloud Storage bucket.
    """
    bucket: storage.Bucket
    source_destination: str
    shutdown_event: threading.Event

    def on_created(self, event):
        """
        Handle file creation events.

        If the created item is a file (not a directory), start a new thread to upload the file.

        Args:
            event (FileSystemEvent): The file system event object.

        """
    
        if event.is_directory:
            return
        local_file_path = event.src_path
        threading.Thread(target=self.upload_file, args=(local_file_path,)).start()

    def upload_file(self, local_file_path):
        """
        Upload a file to the specified Google Cloud Storage bucket.

        Args:
            local_file_path (str): The local path of the file to be uploaded.
        """
        try:
            relative_blob_path = os.path.relpath(local_file_path, self.source_destination)
            destination_blob_name = os.path.join(relative_blob_path)

            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(local_file_path)

            logger.info(f"Uploaded {local_file_path} to {destination_blob_name}")
        except Exception as e:
            logger.error(f"Error uploading {local_file_path}: {e}")


def upload_directory_to_bucket(bucket_name, source_destination, shutdown_event):
    """
    Uploads files from a local directory to a Google Cloud Storage bucket.

    Initializes the Google Cloud Storage client, sets up a thread pool to monitor the local
    directory for file creation events, and uploads the files to the specified bucket.

    Args:
        bucket_name (str): The name of the Google Cloud Storage bucket.
        source_destination (str): The local directory to monitor for file events.
        shutdown_event (threading.Event): Event to signal shutdown.
    """
    try:
        storage_client = storage.Client.from_service_account_json(CREDENTIAL_PATH)
        bucket = storage_client.get_bucket(bucket_name)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            observer = Observer()
            event_handler = FileEventHandler(bucket, source_destination, shutdown_event)
            observer.schedule(event_handler, source_destination, recursive=True)
            observer.start()

            try:
                shutdown_event.wait()
            except KeyboardInterrupt:
                shutdown_event.set()
            finally:
                observer.stop()
                observer.join()

    except Exception as e:
        logger.error(f"Error initializing upload: {e}")

def call_func():
    """
    Initiates the file upload process to Google Cloud Storage.

    Sets up necessary configurations and starts the file upload process in a loop.
    The process can be interrupted by a KeyboardInterrupt.
    """
    GCP_BUCKET_NAME = BUCKET_NAME
    GCP_SOURCE_DESTINATION = SOURCE_DESTINATION
    GCP_CREDENTIAL_PATH = CREDENTIAL_PATH
    shutdown_event = Event()

    while not shutdown_event.is_set():
        try:
            upload_directory_to_bucket(GCP_BUCKET_NAME, GCP_SOURCE_DESTINATION, shutdown_event)
        except KeyboardInterrupt:
            shutdown_event.set()

        time.sleep(1)



  
