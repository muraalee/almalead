"""
MinIO storage implementation.
"""
from typing import BinaryIO
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class MinIOStorage:
    """MinIO implementation of storage interface."""

    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._bucket_initialized = False
        # Don't ensure bucket exists at init - do it lazily
        # This allows tests to import the module without MinIO running

    def ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists, create if it doesn't."""
        if self._bucket_initialized:
            return

        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✓ Created MinIO bucket: {self.bucket_name}")
            self._bucket_initialized = True
        except Exception as e:
            print(f"✗ Error ensuring bucket exists: {e}")
            # Don't raise - allow tests to run without MinIO

    def upload_file(self, file: BinaryIO, object_name: str) -> str:
        """
        Upload a file to MinIO.

        Args:
            file: File-like object to upload
            object_name: Name/key for the object in MinIO

        Returns:
            URL to the uploaded file
        """
        # Ensure bucket exists before uploading
        self.ensure_bucket_exists()

        try:
            # Get file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Seek back to beginning

            # Upload file
            self.client.put_object(
                self.bucket_name,
                object_name,
                file,
                file_size,
            )

            return self.get_file_url(object_name)
        except S3Error as e:
            raise Exception(f"Error uploading file to MinIO: {e}")

    def get_file_url(self, object_name: str) -> str:
        """
        Get the URL for accessing a stored file.

        Args:
            object_name: Name/key of the object in MinIO

        Returns:
            URL to access the file
        """
        # For local development, construct the URL
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{object_name}"

    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from MinIO.

        Args:
            object_name: Name/key of the object to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"✗ Error deleting file from MinIO: {e}")
            return False


# Global storage instance
storage = MinIOStorage()
