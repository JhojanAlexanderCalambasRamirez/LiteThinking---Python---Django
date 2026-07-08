from __future__ import annotations

import re
from dataclasses import dataclass

from litethinking_domain.exceptions import InvalidEmailError

_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
)


@dataclass(frozen=True)
class EmailAddress:
    valor: str

    def __post_init__(self) -> None:
        normalized = self.valor.strip().lower()
        object.__setattr__(self, "valor", normalized)
        if not _EMAIL_PATTERN.match(normalized):
            raise InvalidEmailError(f"'{self.valor}' is not a valid email address.")

    def __str__(self) -> str:
        return self.valor

    @classmethod
    def from_string(cls, value: str) -> EmailAddress:
        return cls(valor=value)
