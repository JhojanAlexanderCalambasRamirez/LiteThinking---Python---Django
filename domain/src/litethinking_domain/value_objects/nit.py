from __future__ import annotations

import re
from dataclasses import dataclass

from litethinking_domain.exceptions import InvalidNITError

_NIT_PATTERN = re.compile(r"^\d{6,10}(-\d)?$")


@dataclass(frozen=True)
class NIT:
    """
    Colombian tax ID. Format: 6-10 digits, optional '-' + 1 check digit.
    Examples: '900123456-7', '9001234567', '123456'
    """

    valor: str

    def __post_init__(self) -> None:
        if not _NIT_PATTERN.match(self.valor):
            raise InvalidNITError(
                f"NIT '{self.valor}' is invalid. "
                "Expected format: 6-10 digits, optionally followed by '-' and a check digit."
            )

    def __str__(self) -> str:
        return self.valor

    @classmethod
    def from_string(cls, value: str) -> NIT:
        return cls(valor=value.strip())
