import boto3
import os
from botocore.exceptions import ClientError
from typing import Optional
import uuid

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'pdf-storage-bucket')
    
    def generate_presigned_url(self, s3_key: str, filename: str) -> str:
        """Generate a pre-signed URL for uploading a PDF file"""
        try:
            # Generate unique S3 key
            file_extension = filename.split('.')[-1] if '.' in filename else 'pdf'
            unique_key = f"pdfs/{uuid.uuid4()}.{file_extension}"
            
            # Generate pre-signed URL for PUT operation
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': unique_key,
                    'ContentType': 'application/pdf'
                },
                ExpiresIn=3600  # URL expires in 1 hour
            )
            
            return presigned_url, unique_key
            
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            raise Exception(f"Error deleting file from S3: {str(e)}")
    
    def get_file_size(self, s3_key: str) -> Optional[int]:
        """Get file size from S3"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response.get('ContentLength')
        except ClientError:
            return None 