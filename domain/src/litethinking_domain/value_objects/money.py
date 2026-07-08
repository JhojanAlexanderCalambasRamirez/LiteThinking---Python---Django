from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from litethinking_domain.exceptions import InvalidMoneyError

_VALID_CURRENCIES = frozenset(
    ["COP", "USD", "EUR", "GBP", "BRL", "MXN", "JPY", "CAD", "CHF", "AUD"]
)


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            except InvalidOperation as exc:
                raise InvalidMoneyError(f"Invalid amount: {self.amount}") from exc

        if self.amount < Decimal("0"):
            raise InvalidMoneyError(
                f"Money amount cannot be negative. Got: {self.amount}"
            )

        normalized_currency = self.currency.strip().upper()
        object.__setattr__(self, "currency", normalized_currency)

        if normalized_currency not in _VALID_CURRENCIES:
            raise InvalidMoneyError(
                f"Currency '{normalized_currency}' is not supported. "
                f"Valid currencies: {sorted(_VALID_CURRENCIES)}"
            )

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise InvalidMoneyError(
                f"Cannot add {self.currency} and {other.currency}. Currency mismatch."
            )
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __str__(self) -> str:
        return f"{self.amount:.4f} {self.currency}"

    def __repr__(self) -> str:
        return f"Money(amount={self.amount}, currency='{self.currency}')"

    @classmethod
    def of(cls, amount: int | float | str | Decimal, currency: str) -> Money:
        try:
            return cls(amount=Decimal(str(amount)), currency=currency)
        except InvalidOperation as exc:
            raise InvalidMoneyError(f"Invalid amount: '{amount}'") from exc
