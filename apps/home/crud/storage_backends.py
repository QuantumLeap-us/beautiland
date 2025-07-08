from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
from botocore.exceptions import NoCredentialsError, ClientError
import os, base64
from django.http import HttpResponse
import boto3
from botocore.exceptions import NoCredentialsError


# Create an S3 client
s3 = boto3.client(
    's3',
    #aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    #aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    #region_name=settings.AWS_S3_REGION_NAME
)

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket.

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name is not specified, use file_name
    if object_name is None:
        object_name = file_name

    try:
        s3.upload_file(file_name, bucket, object_name)
    except FileNotFoundError as e:
        print("The file was not found", e)
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False
    return True


def check_file_exists(bucket_name, object_name):
    """Check if a file exists in an S3 bucket."""
    try:
        s3.head_object(Bucket=bucket_name, Key=object_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            print(f"Error checking file existence: {e}")
            return False


def download_file(bucket, object_name, file_name):
    """Download a file from an S3 bucket.

    :param bucket: Bucket to download from
    :param object_name: S3 object name
    :param file_name: Local file name to save as
    :return: True if file was downloaded, else False
    """
    
    try:
        # Get the object from S3
        s3_object = s3.get_object(Bucket=bucket, Key=object_name)
        
        # Get the file content
        file_content = s3_object['Body'].read()

        # Create a HTTP response
        response = HttpResponse(file_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename={os.path.basename(object_name)}'
        return response
    except NoCredentialsError:
        return HttpResponse("Credentials not available", status=401)
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return HttpResponse("The object does not exist in the bucket", status=404)
        else:
            return HttpResponse(f"Error downloading file: {e}", status=500)


def get_file(bucket, object_name):
    try:
        # Get the object from S3
        s3_object = s3.get_object(Bucket=bucket, Key=object_name)
        
        # Get the file content
        file_content = s3_object['Body'].read()
        base64_str = base64.b64encode(file_content).decode("utf-8")
        base64_with_prefix = "data:image/jpeg;base64," + base64_str 
        return base64_with_prefix
    except NoCredentialsError:
        return HttpResponse("Credentials not available", status=401)
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return HttpResponse("The object does not exist in the bucket", status=404)
        else:
            print("okkkook", e)
            return HttpResponse(f"Error fetching file: {e}", status=500)
    except Exception as e:
        print("errororor", e)


def delete_file(bucket, object_name):
    """Delete a file from an S3 bucket.

    :param bucket: Bucket to delete from
    :param object_name: S3 object name to delete
    :return: True if file was deleted, else False
    """
    try:
        # Delete the file
        s3.delete_object(Bucket=bucket, Key=object_name)
    except NoCredentialsError:
        print("Credentials not available")
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False
    return True


def create_bucket(bucket_name):
    """Create an S3 bucket if it doesn't exist.

    :param bucket_name: Name of the bucket to create
    :return: True if bucket was created or already exists, False otherwise
    """

    try:
        # Check if bucket already exists
        response = s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            # Bucket does not exist, attempt to create it
            try:
                s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': settings.AWS_S3_REGION_NAME})
                print(f"Bucket '{bucket_name}' created successfully.")
                return True
            except NoCredentialsError as e:
                print("Credentials not available: {e}")
                return False
            except ClientError as e:
                print(f"An error occurred: {e.response['Error']['Message']}")
                return False
        else:
            print(f"An unexpected error occurred: {e.response['Error']['Message']}")
            return False
