from html import escape

from app.schemas.public_lookup import PublicLookupResponse


TELEGRAM_CAPTION_LIMIT = 1024
TELEGRAM_TEXT_LIMIT = 4096


def build_lookup_caption(result: PublicLookupResponse) -> str:
    lines: list[str] = []

    if result.title:
        lines.append(f"<b>{escape(result.title)}</b>")

    meta_lines: list[str] = []
    if result.genre:
        meta_lines.append(f"Жанр: {escape(_humanize_genre(result.genre))}")
    if result.season_number is not None:
        meta_lines.append(f"Сезон {result.season_number}")
    if result.episode_number is not None:
        meta_lines.append(f"Серия {result.episode_number}")
    if meta_lines:
        lines.append("\n".join(meta_lines))

    lines.append(f"Код: <code>{escape(result.code)}</code>")

    caption = "\n\n".join(lines).strip()
    return _truncate_text(caption, TELEGRAM_CAPTION_LIMIT)


def build_lookup_text(result: PublicLookupResponse) -> str:
    lines: list[str] = []

    if result.title:
        lines.append(f"<b>{escape(result.title)}</b>")
    if result.genre:
        lines.append(f"Жанр: {escape(_humanize_genre(result.genre))}")
    if result.season_number is not None:
        lines.append(f"Сезон: {result.season_number}")
    if result.episode_number is not None:
        lines.append(f"Серия: {result.episode_number}")
    lines.append("")
    lines.append(f"Код: <code>{escape(result.code)}</code>")
    if result.external_url:
        lines.append(f"Ссылка: {escape(result.external_url)}")

    text = "\n".join(lines).strip()
    return _truncate_text(text, TELEGRAM_TEXT_LIMIT)


def _humanize_genre(value: str) -> str:
    mapping = {
        "anime": "Аниме",
        "series": "Сериал",
        "movie": "Фильм",
    }
    return mapping.get(value, value)


def _truncate_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"
