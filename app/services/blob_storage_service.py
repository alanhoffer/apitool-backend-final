import logging
import os
import tempfile
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
        self.public_base_url = (os.getenv("BLOB_PUBLIC_BASE_URL") or "").strip().rstrip("/")
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

        self.upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.upload_dir / Path(filename).name
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{file_path.name}.",
            suffix=".tmp",
            dir=self.upload_dir,
        )
        try:
            with os.fdopen(fd, "wb") as tmp_file:
                tmp_file.write(body)
            os.replace(tmp_name, file_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
            raise
        return file_path.name

    def local_path_for(self, image_ref: str | None) -> Path | None:
        if not image_ref or image_ref == DEFAULT_APIARY_IMAGE or is_public_url(image_ref):
            return None

        return self.upload_dir / Path(image_ref).name

    def resolve_public_url(self, image_ref: str) -> str | None:
        if not image_ref or image_ref == DEFAULT_APIARY_IMAGE:
            return None

        if is_public_url(image_ref):
            return image_ref

        if self.public_base_url and is_blob_path(image_ref):
            return f"https://{self.public_base_url}/{image_ref.lstrip('/')}"

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

    def resolve_best_image_reference(self, image_ref: str | None) -> str | None:
        if not image_ref:
            return image_ref

        return self.resolve_public_url(image_ref) or image_ref

    def delete_image(self, image_ref: str | None) -> None:
        if not image_ref or image_ref == DEFAULT_APIARY_IMAGE:
            return

        if is_public_url(image_ref) or is_blob_path(image_ref):
            if not self.is_enabled():
                self._delete_local_fallback(image_ref)
                return

            try:
                from vercel.blob import delete

                delete(image_ref, token=self.token)
            except ImportError:
                logger.warning("Python package 'vercel' is not installed. Cannot delete blob '%s'.", image_ref)
            except Exception as exc:
                logger.warning("Could not delete blob '%s': %s", image_ref, exc)
            self._delete_local_fallback(image_ref)
            return

        self._delete_local_fallback(image_ref)

    def _delete_local_fallback(self, image_ref: str | None) -> None:
        file_path = self.local_path_for(image_ref)
        if not file_path:
            return

        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as exc:
            logger.warning("Could not delete local image '%s': %s", image_ref, exc)
