import pickle
import os
import boto3
def lambda_handler(event, context):
    email = os.environ.get("email")
    bucket_name = os.environ.get("bucket_name")
    object_key = f"{email}.jr"
    local_file_path = f"/tmp/{email}.jr"
    
    s3 = boto3.client("s3")
    s3.download_file(bucket_name, object_key, local_file_path)
    with open(local_file_path, "rb") as f:
        cookies = pickle.load(f)

    # import after finished with boto3, otherwise shows
    # Error: Runtime exited with error: signal: segmentation fault
    from linkedin_api import Linkedin
    try:
        api = Linkedin(email, "", cookies=cookies)
        profile = api.get_profile()
        return {
            "statusCode": 200,
            "body": f"Authenticated Successfully."
        }
    except Exception as e:
        print(f"Authentication failed: {e}")
        return {
            "statusCode": 500,
            "body": f"Authentication failed: {e}"
        }

