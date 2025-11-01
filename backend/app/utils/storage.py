"""
Storage abstraction interface.
"""
from typing import Protocol, BinaryIO


class StorageInterface(Protocol):
    """Protocol/Interface for object storage implementations."""

    def upload_file(self, file: BinaryIO, object_name: str) -> str:
        """
        Upload a file to storage.

        Args:
            file: File-like object to upload
            object_name: Name/key for the object in storage

        Returns:
            URL or path to the uploaded file
        """
        ...

    def get_file_url(self, object_name: str) -> str:
        """
        Get the URL for accessing a stored file.

        Args:
            object_name: Name/key of the object in storage

        Returns:
            URL to access the file
        """
        ...

    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from storage.

        Args:
            object_name: Name/key of the object to delete

        Returns:
            True if successful, False otherwise
        """
        ...

    def ensure_bucket_exists(self) -> None:
        """Ensure the storage bucket exists, create if it doesn't."""
        ...
