from google.cloud import storage 

#create a storage client instance
client = storage.Client()

#set up authentication
#listing all buckets 
print("Listing all bucket: ")
buckets = client.list_buckets()

for bucket in buckets:
    print(bucket.name)
    
# listing files in the buckets
bucket = client.bucket("mongodb-0001")
print("*************")
print("listing files....")
for blob in bucket.list_blobs():
    print(blob.name)


#Downloading a blob to a local file 
#blob = bucket.blob("file.txt")
#blob.download_to_filename("example.txt")

# Upload file to the bucket 
print("\n*************")
print("Uploading file to bucket...")
zip_file_path = "/home/tuancuong112504/prj5-gcp/exports/data_export_20260506_113132.zip"
bucket_blob_name = "exports/data_export_20260506_113132.zip"

new_blob = bucket.blob(bucket_blob_name)
new_blob.upload_from_filename(zip_file_path)
print(f"✓ File uploaded successfully: gs://mongodb-0001/{bucket_blob_name}")

# List files in bucket after upload
print("\n*************")
print("Files in bucket after upload:")
for blob in bucket.list_blobs():
    print(f"  - {blob.name} ({blob.size} bytes)")

