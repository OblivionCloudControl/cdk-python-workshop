import boto3
import os
from datetime import datetime

s3 = boto3.resource("s3")
put_bucket_name = os.environ["PUT_BUCKET_NAME"]

def handler(event, context):
  object_name = datetime.now().isoformat() + ".txt"

  object = s3.Object(put_bucket_name, object_name)
  object.put(Body=b"Hello World!")
