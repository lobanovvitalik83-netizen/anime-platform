from html import escape

from app.schemas.public_lookup import PublicLookupResponse


TELEGRAM_CAPTION_LIMIT = 1024
TELEGRAM_TEXT_LIMIT = 4096
VK_TEXT_LIMIT = 4096


def build_lookup_caption(result: PublicLookupResponse) -> str:
    return _truncate_text(_compose_lines(result, html_mode=True), TELEGRAM_CAPTION_LIMIT)


def build_lookup_text(result: PublicLookupResponse) -> str:
    return _truncate_text(_compose_lines(result, html_mode=True), TELEGRAM_TEXT_LIMIT)


def build_lookup_plain_text(result: PublicLookupResponse) -> str:
    return _truncate_text(_compose_lines(result, html_mode=False), VK_TEXT_LIMIT)


def _compose_lines(result: PublicLookupResponse, *, html_mode: bool) -> str:
    lines: list[str] = []

    if result.title:
        title = escape(result.title) if html_mode else result.title
        lines.append(f"<b>{title}</b>" if html_mode else title)
    if result.genre:
        genre_value = _humanize_genre(result.genre)
        genre = escape(genre_value) if html_mode else genre_value
        lines.append(f"Жанр: {genre}")
    if result.season_number is not None:
        lines.append(f"Сезон: {result.season_number}")
    if result.episode_number is not None:
        lines.append(f"Серия: {result.episode_number}")

    lines.append("")
    code_value = escape(result.code) if html_mode else result.code
    lines.append(f"Код: <code>{code_value}</code>" if html_mode else f"Код: {code_value}")

    return "\n".join(lines).strip()


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
