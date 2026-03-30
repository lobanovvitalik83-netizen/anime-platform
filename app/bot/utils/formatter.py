from html import escape

from app.schemas.public_lookup import PublicLookupResponse


TELEGRAM_CAPTION_LIMIT = 1024
TELEGRAM_TEXT_LIMIT = 4096


def build_lookup_caption(result: PublicLookupResponse) -> str:
    return _truncate_text(_build_message(result, html_mode=True, include_link=False), TELEGRAM_CAPTION_LIMIT)


def build_lookup_text(result: PublicLookupResponse) -> str:
    return _truncate_text(_build_message(result, html_mode=True, include_link=True), TELEGRAM_TEXT_LIMIT)


def build_lookup_plain_text(result: PublicLookupResponse) -> str:
    return _truncate_text(_build_message(result, html_mode=False, include_link=True), TELEGRAM_TEXT_LIMIT)


def _build_message(result: PublicLookupResponse, *, html_mode: bool, include_link: bool) -> str:
    lines: list[str] = []

    if result.title:
        title = _format_text(result.title, html_mode=html_mode)
        lines.append(f"<b>{title}</b>" if html_mode else title)

    if result.genre:
        lines.append(f"Жанр: {_format_text(_humanize_genre(result.genre), html_mode=html_mode)}")

    season_episode = _season_episode_line(result)
    if season_episode:
        lines.append(_format_text(season_episode, html_mode=html_mode))

    lines.append("")
    code_value = _format_text(result.code, html_mode=html_mode)
    lines.append(f"Код: <code>{code_value}</code>" if html_mode else f"Код: {code_value}")

    if include_link and result.external_url:
        lines.append(f"Ссылка: {_format_text(result.external_url, html_mode=html_mode)}")

    return "\n".join(lines).strip()


def _season_episode_line(result: PublicLookupResponse) -> str | None:
    season = result.season_number
    episode = result.episode_number
    if season is not None and episode is not None:
        return f"Сезон: {season} · Серия: {episode}"
    if season is not None:
        return f"Сезон: {season}"
    if episode is not None:
        return f"Серия: {episode}"
    return None


def _format_text(value: str, *, html_mode: bool) -> str:
    return escape(value) if html_mode else value


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
