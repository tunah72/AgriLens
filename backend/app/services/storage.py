"""
Storage Service — MinIO object storage.
"""

import io
import os
import uuid
from datetime import timedelta

from minio import Minio


class StorageService:
    """MinIO object storage service for leaf image assets."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        """Initialize MinIO client and ensure default bucket exists."""
        self.client = Minio(endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self.bucket = bucket

        # Ensure default bucket exists
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            # Log warning without crashing during initialization if MinIO is not yet ready
            print(f"Warning: Failed to verify/create MinIO bucket '{self.bucket}': {e}")

    def upload_image(self, image_bytes: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        """Upload image bytes to MinIO and return unique object key."""
        # Prevent filename collisions by assigning UUID
        ext = os.path.splitext(filename)[1] or ".jpg"
        object_key = f"{uuid.uuid4()}{ext}"

        data = io.BytesIO(image_bytes)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_key,
            data=data,
            length=len(image_bytes),
            content_type=content_type,
        )
        return object_key

    def get_url(self, object_key: str, expires_hours: int = 24) -> str:
        """Generate public URL for client-side display via backend proxy."""
        from backend.app.config import settings

        prefix = getattr(settings, "PUBLIC_IMAGE_URL_PREFIX", "/api/v1/images").rstrip("/")
        return f"{prefix}/{object_key}"

    def get_presigned_url(self, object_key: str, expires_hours: int = 24) -> str:
        """Generate presigned URL for direct client-side downloads from MinIO."""
        return self.client.presigned_get_object(
            bucket_name=self.bucket, object_name=object_key, expires=timedelta(hours=expires_hours)
        )

    def get_image(self, object_key: str) -> tuple[bytes, str]:
        """Fetch image bytes and content type from MinIO."""
        response = None
        try:
            response = self.client.get_object(self.bucket, object_key)
            content_type = response.headers.get("content-type", "image/jpeg")
            return response.read(), content_type
        finally:
            if response is not None:
                response.close()
                response.release_conn()
    def delete_image(self, object_key: str) -> None:
        """Delete image from MinIO (used for orphan cleanup on database failure)."""
        try:
            self.client.remove_object(self.bucket, object_key)
        except Exception as e:
            print(f"Warning: Failed to delete image '{object_key}' from MinIO: {e}")
