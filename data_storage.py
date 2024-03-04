import os
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from config import MAX_WORKERS, BUCKET_NAME, CREDENTIAL_PATH, SOURCE_DESTINATION

def upload_file(bucket, local_file_path, SOURCE_DESTINATION):
    relative_blob_path = os.path.relpath(local_file_path, SOURCE_DESTINATION)
    destination_blob_name = os.path.join(relative_blob_path)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)

    print(f"Uploaded {local_file_path} to {destination_blob_name}")

def upload_directory_to_bucket(BUCKET_NAME, SOURCE_DESTINATION, CREDENTIAL_PATH):
    storage_client = storage.Client.from_service_account_json(CREDENTIAL_PATH)
    bucket = storage_client.get_bucket(BUCKET_NAME)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:  
        futures = []

        for root, dirs, files in os.walk(SOURCE_DESTINATION):
            for file in files:
                local_file_path = os.path.join(root, file)
                futures.append(executor.submit(upload_file, bucket, local_file_path, SOURCE_DESTINATION))

        for future in futures:
            future.result()

if __name__ == "__main__":
    BUCKET_NAME = BUCKET_NAME
    SOURCE_DESTINATION = SOURCE_DESTINATION
    CREDENTIAL_PATH = CREDENTIAL_PATH
    upload_directory_to_bucket(BUCKET_NAME, SOURCE_DESTINATION, CREDENTIAL_PATH)
