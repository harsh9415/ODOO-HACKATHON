"""Text utility helpers."""


def get_company_initials(company_name: str) -> str:
    words = company_name.strip().split()
    return "".join(w[0].upper() for w in words if w)


def get_name_initials(first_name: str, last_name: str) -> str:
    fn = (first_name or "")[:2].upper().ljust(2, "X")
    ln = (last_name or "")[:2].upper().ljust(2, "X")
    return fn + ln


def normalize_login_id(login_id: str) -> str:
    """Normalize user input login ID to handle case-insensitivity and common 0I vs OI typos."""
    val = (login_id or "").strip()
    if "@" not in val:
        val = val.upper()
        if val.startswith("0I"):
            val = "O" + val[1:]
    else:
        val = val.lower()
    return val


import re

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Verify that password follows security rules:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""
