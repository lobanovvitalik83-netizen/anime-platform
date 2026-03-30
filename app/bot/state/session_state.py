USER_MODE_LOOKUP = "lookup"
USER_MODE_REPORT = "report"

_user_modes: dict[int, str] = {}

def set_user_mode(user_id: int, mode: str) -> None:
    _user_modes[user_id] = mode

def get_user_mode(user_id: int) -> str | None:
    return _user_modes.get(user_id)

def clear_user_mode(user_id: int) -> None:
    _user_modes.pop(user_id, None)
