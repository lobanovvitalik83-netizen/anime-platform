import re


GENRE_PREFIX_PATTERN = re.compile(r"^\[\[genre:(.*?)\]\]\n?", re.IGNORECASE | re.DOTALL)


def pack_title_description(genre: str | None, description: str | None) -> str | None:
    genre = (genre or "").strip()
    description = (description or "").strip()
    if genre:
        if description:
            return f"[[genre:{genre}]]\n{description}"
        return f"[[genre:{genre}]]"
    return description or None


def unpack_title_description(raw_description: str | None) -> tuple[str | None, str | None]:
    raw_description = raw_description or ""
    raw_description = raw_description.strip()
    if not raw_description:
        return None, None

    match = GENRE_PREFIX_PATTERN.match(raw_description)
    if not match:
        return None, raw_description

    genre = match.group(1).strip() or None
    cleaned = GENRE_PREFIX_PATTERN.sub("", raw_description, count=1).strip() or None
    return genre, cleaned
