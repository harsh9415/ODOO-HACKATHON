from __future__ import annotations

"""Generate temporary passwords for new employees."""

import secrets
import string


def generate_temp_password(length: int = 12) -> str:
    """Generate a random password with mixed case, digits, and symbols."""
    if length < 10:
        length = 10

    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%&*"

    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]

    all_chars = lowercase + uppercase + digits + symbols
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    secrets.SystemRandom().shuffle(password)
    return "".join(password)
