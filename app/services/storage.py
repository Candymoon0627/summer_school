from pathlib import Path
from urllib.parse import quote

import httpx

from app.core.config import get_settings


class StorageService:
    def put_file(self, local_path: Path, object_key: str) -> str:
        settings = get_settings()
        if settings.storage_provider == "supabase":
            self._put_supabase_file(local_path, object_key)
            return object_key
        if settings.storage_provider != "local":
            raise ValueError(f"Unsupported storage provider: {settings.storage_provider}")

        target = settings.local_storage_dir / object_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(local_path.read_bytes())
        return object_key

    def signed_url(self, object_key: str, expires_in: int = 3600) -> str:
        settings = get_settings()
        if settings.storage_provider == "local":
            return str((settings.local_storage_dir / object_key).resolve())
        if settings.storage_provider == "supabase":
            return self._supabase_signed_url(object_key, expires_in=expires_in)
        raise ValueError(f"Unsupported storage provider: {settings.storage_provider}")

    def delete_file(self, object_key: str) -> None:
        settings = get_settings()
        if settings.storage_provider == "local":
            path = settings.local_storage_dir / object_key
            if path.exists():
                path.unlink()
            return
        if settings.storage_provider == "supabase":
            self._delete_supabase_file(object_key)
            return
        raise ValueError(f"Unsupported storage provider: {settings.storage_provider}")

    def _put_supabase_file(self, local_path: Path, object_key: str) -> None:
        base_url, headers, bucket = self._supabase_config()
        content_type = self._content_type(local_path)
        url = f"{base_url}/storage/v1/object/{bucket}/{self._quote_object_key(object_key)}"
        with httpx.Client(timeout=60) as client:
            response = client.post(
                url,
                content=local_path.read_bytes(),
                headers=headers | {"content-type": content_type, "x-upsert": "true"},
            )
        response.raise_for_status()

    def _supabase_signed_url(self, object_key: str, *, expires_in: int) -> str:
        base_url, headers, bucket = self._supabase_config()
        url = f"{base_url}/storage/v1/object/sign/{bucket}/{self._quote_object_key(object_key)}"
        with httpx.Client(timeout=30) as client:
            response = client.post(url, json={"expiresIn": expires_in}, headers=headers)
        response.raise_for_status()
        data = response.json()
        signed_url = data.get("signedURL") or data.get("signedUrl")
        if not signed_url:
            raise ValueError("Supabase did not return a signed URL.")
        if signed_url.startswith("/"):
            return f"{base_url}/storage/v1{signed_url}"
        return signed_url

    def _delete_supabase_file(self, object_key: str) -> None:
        base_url, headers, bucket = self._supabase_config()
        url = f"{base_url}/storage/v1/object/{bucket}/{self._quote_object_key(object_key)}"
        with httpx.Client(timeout=30) as client:
            response = client.delete(url, headers=headers)
        response.raise_for_status()

    def _supabase_config(self) -> tuple[str, dict[str, str], str]:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for Supabase storage."
            )
        base_url = settings.supabase_url.rstrip("/")
        key = settings.supabase_service_role_key
        headers = {"Authorization": f"Bearer {key}", "apikey": key}
        return base_url, headers, settings.supabase_storage_bucket

    def _quote_object_key(self, object_key: str) -> str:
        return "/".join(quote(part, safe="") for part in object_key.split("/"))

    def _content_type(self, local_path: Path) -> str:
        suffix = local_path.suffix.lower()
        if suffix == ".docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if suffix == ".pdf":
            return "application/pdf"
        if suffix in {".txt", ".md"}:
            return "text/plain; charset=utf-8"
        return "application/octet-stream"
