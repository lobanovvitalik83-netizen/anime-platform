USER_MODE_LOOKUP = "lookup"
USER_MODE_REPORT = "report"

_USER_MODES: dict[int, str] = {}


def set_user_mode(user_id: int, mode: str) -> None:
    _USER_MODES[user_id] = mode


def get_user_mode(user_id: int) -> str | None:
    return _USER_MODES.get(user_id)


def clear_user_mode(user_id: int) -> None:
    _USER_MODES.pop(user_id, None)
