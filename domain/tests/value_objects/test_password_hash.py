import pytest

from litethinking_domain.exceptions import InvalidPasswordHashError
from litethinking_domain.value_objects.password_hash import PasswordHash


BCRYPT_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lewdx9sCHkRrIc2Vy"
BCRYPT_A_HASH = "$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lewdx9sCHkRrIc2Vy"
ARGON2_DIRECT = "$argon2id$v=19$m=65536,t=3,p=4$abc$xyz"
ARGON2_DJANGO = "argon2$argon2id$v=19$m=65536,t=3,p=4$abc$xyz"
BCRYPT_DJANGO = "bcrypt$2b$12$abcdefghij"
BCRYPT_SHA256 = "bcrypt_sha256$2b$12$abcdefghij"


class TestPasswordHashValidPrefixes:
    def test_bcrypt_2b(self) -> None:
        ph = PasswordHash(BCRYPT_HASH)
        assert ph.valor == BCRYPT_HASH

    def test_bcrypt_2a(self) -> None:
        PasswordHash(BCRYPT_A_HASH)

    def test_argon2_direct(self) -> None:
        PasswordHash(ARGON2_DIRECT)

    def test_argon2_django_prefix(self) -> None:
        PasswordHash(ARGON2_DJANGO)

    def test_bcrypt_django_prefix(self) -> None:
        PasswordHash(BCRYPT_DJANGO)

    def test_bcrypt_sha256_prefix(self) -> None:
        PasswordHash(BCRYPT_SHA256)

    def test_from_hashed_string_factory(self) -> None:
        ph = PasswordHash.from_hashed_string(BCRYPT_HASH)
        assert ph.valor == BCRYPT_HASH


class TestPasswordHashInvalidValues:
    def test_plaintext_raises(self) -> None:
        with pytest.raises(InvalidPasswordHashError):
            PasswordHash("mypassword")

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidPasswordHashError):
            PasswordHash("")

    def test_md5_raises(self) -> None:
        with pytest.raises(InvalidPasswordHashError):
            PasswordHash("5f4dcc3b5aa765d61d8327deb882cf99")

    def test_sha256_raises(self) -> None:
        with pytest.raises(InvalidPasswordHashError):
            PasswordHash("ef92b778bafe771207987aa3a86abb1b0a282a1e2e5cf8b3b7c2d5bcd2e8c2b0")

    def test_partial_prefix_raises(self) -> None:
        with pytest.raises(InvalidPasswordHashError):
            PasswordHash("$2c$12$notvalid")


class TestPasswordHashSafety:
    def test_repr_redacted(self) -> None:
        ph = PasswordHash(BCRYPT_HASH)
        assert BCRYPT_HASH not in repr(ph)
        assert "redacted" in repr(ph)

    def test_str_returns_hash(self) -> None:
        ph = PasswordHash(BCRYPT_HASH)
        assert str(ph) == BCRYPT_HASH

    def test_frozen_dataclass(self) -> None:
        ph = PasswordHash(BCRYPT_HASH)
        with pytest.raises((AttributeError, TypeError)):
            ph.valor = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        assert PasswordHash(BCRYPT_HASH) == PasswordHash(BCRYPT_HASH)

    def test_inequality_different_hashes(self) -> None:
        assert PasswordHash(BCRYPT_HASH) != PasswordHash(BCRYPT_A_HASH)
