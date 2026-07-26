import bcrypt

MINIMUM_LENGTH = 10

# bcrypt hashes at most 72 bytes and discards the rest without complaining. Refusing longer
# input is honest; silently ignoring the tail would let someone believe a long passphrase is
# protecting them when only its beginning is.
MAXIMUM_BYTES = 72


class PasswordRejectedError(ValueError):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_encode(password), password_hash.encode())
    except (PasswordRejectedError, ValueError):
        return False


def describe_requirements() -> str:
    return f"Parola trebuie să aibă cel puțin {MINIMUM_LENGTH} caractere."


def _encode(password: str) -> bytes:
    if len(password) < MINIMUM_LENGTH:
        raise PasswordRejectedError(describe_requirements())

    encoded = password.encode("utf-8")
    if len(encoded) > MAXIMUM_BYTES:
        raise PasswordRejectedError(
            f"Parola este prea lungă: cel mult {MAXIMUM_BYTES} de octeți "
            "(diacriticele ocupă câte doi)."
        )
    return encoded
