from html import escape

from app.schemas.public_lookup import PublicLookupResponse


TELEGRAM_CAPTION_LIMIT = 1024
TELEGRAM_TEXT_LIMIT = 4096


def build_lookup_caption(result: PublicLookupResponse) -> str:
    lines = _build_lines(result, rich_text=True)
    caption = "\n".join(lines).strip()
    return _truncate_text(caption, TELEGRAM_CAPTION_LIMIT)


def build_lookup_text(result: PublicLookupResponse) -> str:
    lines = _build_lines(result, rich_text=True)
    text = "\n".join(lines).strip()
    return _truncate_text(text, TELEGRAM_TEXT_LIMIT)


def build_lookup_plain_text(result: PublicLookupResponse) -> str:
    return "\n".join(_build_lines(result, rich_text=False)).strip()


def _build_lines(result: PublicLookupResponse, *, rich_text: bool) -> list[str]:
    lines: list[str] = []

    if result.title:
        title = escape(result.title) if rich_text else result.title
        lines.append(f"<b>{title}</b>" if rich_text else title)

    if result.genre:
        genre = _humanize_genre(result.genre)
        lines.append(f"Жанр: {escape(genre) if rich_text else genre}")

    if result.season_number is not None:
        lines.append(f"Сезон: {result.season_number}")

    if result.episode_number is not None:
        lines.append(f"Серия: {result.episode_number}")

    lines.append("")
    code_value = escape(result.code) if rich_text else result.code
    lines.append(f"Код: <code>{code_value}</code>" if rich_text else f"Код: {code_value}")
    return lines


def _humanize_genre(value: str) -> str:
    mapping = {
        'anime': 'Аниме',
        'series': 'Сериал',
        'movie': 'Фильм',
    }
    return mapping.get(value, value)


def _truncate_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + '…'
