import mimetypes
from pathlib import Path

from app.database import SessionLocal
from app.models.apiary import Apiary
from app.services.blob_storage_service import (
    BlobStorageService,
    DEFAULT_APIARY_IMAGE,
    is_blob_path,
    is_public_url,
)


def main() -> None:
    storage = BlobStorageService()
    if not storage.is_enabled():
        raise SystemExit("BLOB_READ_WRITE_TOKEN is required to migrate images to Vercel Blob.")

    upload_dir = storage.upload_dir
    db = SessionLocal()
    migrated = 0
    skipped = 0
    missing = 0

    try:
        apiaries = db.query(Apiary).all()
        for apiary in apiaries:
            image_ref = apiary.image
            if not image_ref or image_ref == DEFAULT_APIARY_IMAGE:
                skipped += 1
                continue

            if is_blob_path(image_ref) or is_public_url(image_ref):
                skipped += 1
                continue

            file_path = upload_dir / Path(image_ref).name
            if not file_path.exists():
                print(f"[WARN] Missing local image for apiary {apiary.id}: {image_ref}")
                missing += 1
                continue

            blob_path = f"apiarys/{file_path.name}"
            existing_url = storage.resolve_public_url(blob_path)
            if existing_url:
                apiary.image = blob_path
                migrated += 1
                print(f"[OK] Reused existing blob for apiary {apiary.id}: {blob_path}")
                continue

            content_type = mimetypes.guess_type(file_path.name)[0] or "image/jpeg"
            uploaded_path = storage.upload_apiary_image(
                file_path.read_bytes(),
                filename=file_path.name,
                content_type=content_type,
            )
            apiary.image = uploaded_path
            migrated += 1
            print(f"[OK] Migrated apiary {apiary.id}: {image_ref} -> {uploaded_path}")

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("")
    print(f"Migrated: {migrated}")
    print(f"Skipped: {skipped}")
    print(f"Missing: {missing}")


if __name__ == "__main__":
    main()
