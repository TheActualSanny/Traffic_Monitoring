import os
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from config import MAX_WORKERS, BUCKET_NAME, CREDENTIAL_PATH, SOURCE_DESTINATION
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Event

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, bucket, source_destination, shutdown_event):
        self.bucket = bucket
        self.source_destination = source_destination
        self.shutdown_event = shutdown_event

    def on_created(self, event):
        if event.is_directory:
            return
        local_file_path = event.src_path
        upload_file(self.bucket, local_file_path, self.source_destination)

def upload_file(bucket, local_file_path, source_destination):
    relative_blob_path = os.path.relpath(local_file_path, source_destination)
    destination_blob_name = os.path.join(relative_blob_path)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)

    print(f"Uploaded {local_file_path} to {destination_blob_name}")
    os.remove(local_file_path)
    print(f"Deleted local file: {local_file_path}")

def upload_directory_to_bucket(bucket_name, source_destination, credential_path, shutdown_event):
    storage_client = storage.Client.from_service_account_json(credential_path)
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

def call_func():
    GCP_BUCKET_NAME = BUCKET_NAME
    GCP_SOURCE_DESTINATION = SOURCE_DESTINATION
    GCP_CREDENTIAL_PATH = CREDENTIAL_PATH
    shutdown_event = Event()

    try:
        upload_directory_to_bucket(GCP_BUCKET_NAME, GCP_SOURCE_DESTINATION, GCP_CREDENTIAL_PATH, shutdown_event)
    except KeyboardInterrupt:
        shutdown_event.set()

call_func()