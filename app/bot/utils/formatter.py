from html import escape

from app.schemas.public_lookup import PublicLookupResponse


TELEGRAM_CAPTION_LIMIT = 1024
TELEGRAM_TEXT_LIMIT = 4096


def build_lookup_caption(result: PublicLookupResponse) -> str:
    lines: list[str] = []

    title_parts: list[str] = []
    if result.title:
        title_parts.append(f"<b>{escape(result.title)}</b>")
    if result.original_title:
        title_parts.append(escape(result.original_title))
    if result.year:
        title_parts.append(str(result.year))
    if title_parts:
        lines.append("\n".join(title_parts))

    meta_lines: list[str] = []
    if result.genre:
        meta_lines.append(f"Жанр: {escape(result.genre)}")
    if result.title_type:
        meta_lines.append(f"Тип: {escape(result.title_type)}")
    if result.season_number is not None:
        season_text = f"Сезон {result.season_number}"
        if result.season_name:
            season_text += f" — {escape(result.season_name)}"
        meta_lines.append(season_text)
    if result.episode_number is not None:
        episode_text = f"Серия {result.episode_number}"
        if result.episode_name:
            episode_text += f" — {escape(result.episode_name)}"
        meta_lines.append(episode_text)
    if meta_lines:
        lines.append("\n".join(meta_lines))

    if result.description:
        lines.append(_truncate_text(escape(result.description), 700))

    lines.append(f"Код: <code>{escape(result.code)}</code>")

    caption = "\n\n".join(lines).strip()
    return _truncate_text(caption, TELEGRAM_CAPTION_LIMIT)


def build_lookup_text(result: PublicLookupResponse) -> str:
    lines: list[str] = []

    if result.title:
        lines.append(f"<b>{escape(result.title)}</b>")
    if result.original_title:
        lines.append(escape(result.original_title))
    if result.year:
        lines.append(f"Год: {result.year}")
    if result.genre:
        lines.append(f"Жанр: {escape(result.genre)}")
    if result.title_type:
        lines.append(f"Тип: {escape(result.title_type)}")
    if result.season_number is not None:
        season_line = f"Сезон: {result.season_number}"
        if result.season_name:
            season_line += f" — {escape(result.season_name)}"
        lines.append(season_line)
    if result.episode_number is not None:
        episode_line = f"Серия: {result.episode_number}"
        if result.episode_name:
            episode_line += f" — {escape(result.episode_name)}"
        lines.append(episode_line)
    if result.description:
        lines.append("")
        lines.append(_truncate_text(escape(result.description), 2500))
    lines.append("")
    lines.append(f"Код: <code>{escape(result.code)}</code>")
    if result.external_url:
        lines.append(f"Ссылка: {escape(result.external_url)}")

    text = "\n".join(lines).strip()
    return _truncate_text(text, TELEGRAM_TEXT_LIMIT)


def _truncate_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"
