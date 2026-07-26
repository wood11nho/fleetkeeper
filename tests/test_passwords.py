import pytest

from fleetkeeper.security.passwords import (
    MAXIMUM_BYTES,
    MINIMUM_LENGTH,
    PasswordRejectedError,
    hash_password,
    verify_password,
)


def test_a_hashed_password_verifies_against_itself() -> None:
    stored = hash_password("parola-mea-secreta")

    assert verify_password("parola-mea-secreta", stored)
    assert not verify_password("parola-mea-secretă", stored)


def test_the_same_password_hashes_differently_every_time() -> None:
    """Each hash carries its own salt, so identical passwords are not visibly identical."""
    assert hash_password("parola-mea-secreta") != hash_password("parola-mea-secreta")


def test_a_short_password_is_refused() -> None:
    with pytest.raises(PasswordRejectedError):
        hash_password("a" * (MINIMUM_LENGTH - 1))


def test_a_password_past_the_bcrypt_limit_is_refused_rather_than_truncated() -> None:
    """bcrypt discards everything past 72 bytes without a word of warning.

    Accepting such a password would mean two different long passphrases sharing a hash, and
    the owner believing the ignored tail was protecting them.
    """
    with pytest.raises(PasswordRejectedError):
        hash_password("a" * (MAXIMUM_BYTES + 1))


def test_diacritics_count_as_two_bytes_towards_the_limit() -> None:
    with pytest.raises(PasswordRejectedError):
        hash_password("ă" * (MAXIMUM_BYTES // 2 + 1))


def test_verifying_an_impossible_password_fails_instead_of_raising() -> None:
    stored = hash_password("parola-mea-secreta")

    assert not verify_password("a" * (MAXIMUM_BYTES + 1), stored)
    assert not verify_password("scurt", stored)
