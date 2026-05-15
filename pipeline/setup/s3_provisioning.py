import boto3
import logging
from botocore.exceptions import ClientError
from typing import Optional
from dotenv import load_dotenv
import os

# Setup logging for professional feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class S3Manager:
    def __init__(self, profile: str, region: str):
        self.session = boto3.Session(profile_name=profile)
        self.s3_client = self.session.client('s3', region_name=region)
        self.region = region

    def create_bucket(self, bucket_name: str) -> bool:
        """Creates an S3 bucket in a specified region."""
        try:
            logger.info(f"Checking/Creating bucket: {bucket_name}")
            
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            logger.info(f"✅ Bucket {bucket_name} ready.")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyOwnedByYou':
                logger.warning(f"⚠️ Bucket {bucket_name} already exists and is owned by you.")
                return True
            logger.error(f"❌ Failed to create bucket: {e}")
            return False

if __name__ == "__main__":
    load_dotenv()
    
    manager = S3Manager(
        profile=os.getenv("AWS_PROFILE"),
        region=os.getenv("AWS_DEFAULT_REGION")
    )
    
    bucket = os.getenv("S3_BUCKET")
    if bucket:
        manager.create_bucket(bucket)