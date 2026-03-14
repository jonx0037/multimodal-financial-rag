"""
S3-compatible object store wrapper (works with AWS S3 and Cloudflare R2).
All boto3 calls are wrapped in asyncio.to_thread() since boto3 is synchronous.
"""

import asyncio
import logging

import boto3

logger = logging.getLogger(__name__)


class ObjectStore:
    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
    ):
        self.bucket_name = bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    async def upload_file(
        self, file_bytes: bytes, key: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Upload bytes to the bucket and return the storage key."""
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self.bucket_name,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        logger.info("Uploaded %d bytes to s3://%s/%s", len(file_bytes), self.bucket_name, key)
        return key

    async def generate_presigned_url(self, key: str, expiry: int = 3600) -> str:
        """Generate a presigned GET URL for a stored object."""
        url = await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expiry,
        )
        return url

    async def download_file(self, key: str) -> bytes:
        """Download an object and return its bytes."""
        response = await asyncio.to_thread(
            self._client.get_object,
            Bucket=self.bucket_name,
            Key=key,
        )
        return response["Body"].read()
