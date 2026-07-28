from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
import boto3
from botocore.config import Config


class StorageBackend(ABC):
    @abstractmethod
    async def upload(self, bucket: str, key: str, file_path: str | Path) -> str:
        ...

    @abstractmethod
    async def download(self, bucket: str, key: str, dest: str | Path) -> str:
        ...

    @abstractmethod
    async def delete(self, bucket: str, key: str) -> None:
        ...

    @abstractmethod
    async def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        ...

    @abstractmethod
    async def generate_presigned_upload_url(self, bucket: str, key: str, expires_in: int = 3600) -> dict:
        ...


class S3Storage(StorageBackend):
    def __init__(self, endpoint: str, region: str, access_key: str, secret_key: str):
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )

    async def upload(self, bucket: str, key: str, file_path: str | Path) -> str:
        self.client.upload_file(str(file_path), bucket, key)
        return f"{bucket}/{key}"

    async def download(self, bucket: str, key: str, dest: str | Path) -> str:
        self.client.download_file(bucket, key, str(dest))
        return str(dest)

    async def delete(self, bucket: str, key: str) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)

    async def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    async def generate_presigned_upload_url(self, bucket: str, key: str, expires_in: int = 3600) -> dict:
        url = self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return {"url": url, "fields": {}}


def create_storage(
    provider: str = "minio",
    endpoint: str = "http://minio:9000",
    region: str = "us-east-1",
    access_key: str = "clippy",
    secret_key: str = "clippy_secret",
) -> StorageBackend:
    return S3Storage(endpoint, region, access_key, secret_key)
