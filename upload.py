import logging
import boto3
from botocore.exceptions import ClientError


def upload_file(data, file_name, folder, bucket):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    s3 = boto3.resource('s3')
    try:
        file_name = folder + '/' + file_name
        s3.Bucket(bucket).put_object(Key=file_name, Body=data)
    except ClientError as e:
        logging.error(e)
        return False
    return True