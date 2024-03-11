import os
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from config import MAX_WORKERS, BUCKET_NAME, CREDENTIAL_PATH, SOURCE_DESTINATION
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Event
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Event
import os
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Event
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, bucket, source_destination, shutdown_event):
        self.bucket = bucket
        self.source_destination = source_destination
        self.shutdown_event = shutdown_event

    def on_created(self, event):
        if event.is_directory:
            return
        local_file_path = event.src_path
        threading.Thread(target=self.upload_file, args=(local_file_path,)).start()

    def upload_file(self, local_file_path):
        try:
            relative_blob_path = os.path.relpath(local_file_path, self.source_destination)
            destination_blob_name = os.path.join(relative_blob_path)

            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(local_file_path)

            logger.info(f"Uploaded {local_file_path} to {destination_blob_name}")
        except Exception as e:
            logger.error(f"Error uploading {local_file_path}: {e}")


def upload_directory_to_bucket(bucket_name, source_destination, shutdown_event):
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

if __name__ == "__main__":
    call_func()
