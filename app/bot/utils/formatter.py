from html import escape

from app.schemas.public_lookup import PublicLookupResponse


def build_lookup_caption(result: PublicLookupResponse) -> str:
    lines = []

    if result.title:
        title_line = f"<b>{escape(result.title)}</b>"
        if result.original_title:
            title_line += f"\n{escape(result.original_title)}"
        lines.append(title_line)

    meta = []
    if result.season_number is not None:
        season_text = f"Сезон {result.season_number}"
        if result.season_name:
            season_text += f" — {escape(result.season_name)}"
        meta.append(season_text)

    if result.episode_number is not None:
        episode_text = f"Эпизод {result.episode_number}"
        if result.episode_name:
            episode_text += f" — {escape(result.episode_name)}"
        meta.append(episode_text)

    if meta:
        lines.append("\n".join(meta))

    if result.description:
        lines.append(escape(result.description))

    lines.append(f"Код: <code>{escape(result.code)}</code>")

    return "\n\n".join(lines)
