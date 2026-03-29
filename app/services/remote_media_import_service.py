import mimetypes
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from app.core.exceptions import ValidationError


class RemoteMediaImportService:
    def normalize_url(self, url: str) -> str:
        raw = url.strip()
        parsed = urlparse(raw)
        host = parsed.netloc.lower()

        if "drive.google.com" in host:
            file_id = self._extract_drive_file_id(parsed)
            if file_id:
                query = urlencode({"export": "download", "id": file_id})
                return urlunparse(("https", "drive.google.com", "/uc", "", query, ""))

        if "dropbox.com" in host:
            query = parse_qs(parsed.query, keep_blank_values=True)
            query.pop("dl", None)
            query["raw"] = ["1"]
            return urlunparse((parsed.scheme or "https", parsed.netloc, parsed.path, "", urlencode(query, doseq=True), ""))

        return raw

    def fetch(self, url: str, *, max_size_bytes: int) -> tuple[bytes, str, str | None]:
        normalized = self.normalize_url(url)
        request = Request(
            normalized,
            headers={
                "User-Agent": "MediaBridge/1.0",
                "Accept": "*/*",
            },
        )
        with urlopen(request, timeout=30) as response:
            content = response.read(max_size_bytes + 1)
            if len(content) > max_size_bytes:
                raise ValidationError("Файл по ссылке слишком большой для импорта.")

            content_type = response.headers.get_content_type()
            file_name = self._resolve_file_name(response.headers.get("Content-Disposition"), normalized, content_type)
            return content, file_name, content_type

    def _resolve_file_name(self, content_disposition: str | None, url: str, content_type: str | None) -> str:
        if content_disposition and "filename=" in content_disposition:
            raw = content_disposition.split("filename=", 1)[1].strip().strip('"').strip("'")
            if raw:
                return raw

        parsed = urlparse(url)
        name = Path(parsed.path).name
        if name:
            return name

        extension = mimetypes.guess_extension(content_type or "") or ".bin"
        return f"remote-import{extension}"

    def _extract_drive_file_id(self, parsed) -> str | None:
        query = parse_qs(parsed.query)
        if "id" in query and query["id"]:
            return query["id"][0]

        parts = [part for part in parsed.path.split("/") if part]
        if "file" in parts and "d" in parts:
            try:
                idx = parts.index("d")
                return parts[idx + 1]
            except Exception:
                return None
        return None
