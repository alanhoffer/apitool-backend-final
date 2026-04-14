import logging
import os
from pathlib import Path

from app.runtime import get_upload_dir


logger = logging.getLogger(__name__)

DEFAULT_APIARY_IMAGE = "apiary-default.png"


def is_blob_path(value: str | None) -> bool:
    return bool(value) and "/" in value and not value.startswith(("http://", "https://"))


def is_public_url(value: str | None) -> bool:
    return bool(value) and value.startswith(("http://", "https://"))


class BlobStorageService:
    def __init__(self) -> None:
        self.token = os.getenv("BLOB_READ_WRITE_TOKEN")
        self.upload_dir = get_upload_dir()

    def is_enabled(self) -> bool:
        return os.getenv("TESTING") != "1" and bool(self.token)

    def upload_apiary_image(self, body: bytes, *, filename: str, content_type: str) -> str:
        if self.is_enabled():
            try:
                from vercel.blob import put

                blob = put(
                    f"apiarys/{filename}",
                    body,
                    access="public",
                    content_type=content_type,
                    token=self.token,
                )
                return blob.pathname
            except ImportError:
                logger.warning("Python package 'vercel' is not installed. Falling back to local storage.")
            except Exception as exc:
                logger.exception("Failed to upload image to Vercel Blob: %s", exc)
                raise

        file_path = self.upload_dir / filename
        file_path.write_bytes(body)
        return filename

    def resolve_public_url(self, image_ref: str) -> str | None:
        if not image_ref or image_ref == DEFAULT_APIARY_IMAGE:
            return None

        if is_public_url(image_ref):
            return image_ref

        if not self.is_enabled():
            return None

        try:
            from vercel.blob import head

            blob = head(image_ref, token=self.token)
            return blob.url
        except ImportError:
            logger.warning("Python package 'vercel' is not installed. Cannot resolve Vercel Blob URLs.")
            return None
        except Exception as exc:
            logger.warning("Could not resolve blob URL for '%s': %s", image_ref, exc)
            return None

    def delete_image(self, image_ref: str | None) -> None:
        if not image_ref or image_ref == DEFAULT_APIARY_IMAGE:
            return

        if is_public_url(image_ref) or is_blob_path(image_ref):
            if not self.is_enabled():
                return

            try:
                from vercel.blob import delete

                delete(image_ref, token=self.token)
            except ImportError:
                logger.warning("Python package 'vercel' is not installed. Cannot delete blob '%s'.", image_ref)
            except Exception as exc:
                logger.warning("Could not delete blob '%s': %s", image_ref, exc)
            return

        file_path = self.upload_dir / Path(image_ref).name
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as exc:
            logger.warning("Could not delete local image '%s': %s", image_ref, exc)
