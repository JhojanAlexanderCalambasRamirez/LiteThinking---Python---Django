from __future__ import annotations

import re
from dataclasses import dataclass

from litethinking_domain.exceptions import InvalidPasswordHashError

# bcrypt direct:   $2b$... / $2a$...
# argon2 direct:   $argon2id$...
# Django argon2:   argon2$argon2id$...
# Django bcrypt:   bcrypt$... / bcrypt_sha256$...
_VALID_PREFIXES = ("$2b$", "$2a$", "$argon2", "argon2$", "bcrypt$", "bcrypt_sha256$")


@dataclass(frozen=True)
class PasswordHash:
    """
    Opaque value object wrapping a hashed password string.
    Domain only stores the hash - hashing/verification belongs to infrastructure.
    Validates the hash has a recognized format to prevent storing plaintext.
    """

    valor: str

    def __post_init__(self) -> None:
        if not any(self.valor.startswith(prefix) for prefix in _VALID_PREFIXES):
            raise InvalidPasswordHashError(
                "Password must be stored as a bcrypt ($2b$/$2a$) or argon2 hash. "
                "Plaintext passwords are not allowed in the domain."
            )

    def __str__(self) -> str:
        return self.valor

    def __repr__(self) -> str:
        return "PasswordHash(<redacted>)"

    @classmethod
    def from_hashed_string(cls, hashed: str) -> PasswordHash:
        return cls(valor=hashed)
