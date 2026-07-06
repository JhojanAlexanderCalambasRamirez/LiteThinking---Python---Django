from decimal import Decimal

import pytest

from litethinking_domain.exceptions import InvalidMoneyError
from litethinking_domain.value_objects.money import Money, _VALID_CURRENCIES


class TestMoneyCreation:
    def test_valid_cop(self) -> None:
        m = Money(amount=Decimal("100.50"), currency="COP")
        assert m.amount == Decimal("100.50")
        assert m.currency == "COP"

    def test_valid_usd(self) -> None:
        m = Money.of("99.99", "USD")
        assert m.currency == "USD"

    def test_zero_amount_allowed(self) -> None:
        m = Money(amount=Decimal("0"), currency="EUR")
        assert m.amount == Decimal("0")

    def test_currency_normalized_to_uppercase(self) -> None:
        m = Money(amount=Decimal("10"), currency="cop")
        assert m.currency == "COP"

    def test_amount_coerced_from_int(self) -> None:
        m = Money(amount=100, currency="COP")  # type: ignore[arg-type]
        assert isinstance(m.amount, Decimal)

    def test_amount_coerced_from_float_string(self) -> None:
        m = Money.of("19.99", "USD")
        assert m.amount == Decimal("19.99")

    def test_of_factory_all_valid_currencies(self) -> None:
        for currency in _VALID_CURRENCIES:
            m = Money.of(1, currency)
            assert m.currency == currency


class TestMoneyInvalidCreation:
    def test_negative_amount_raises(self) -> None:
        with pytest.raises(InvalidMoneyError, match="negative"):
            Money(amount=Decimal("-1"), currency="COP")

    def test_unknown_currency_raises(self) -> None:
        with pytest.raises(InvalidMoneyError, match="not supported"):
            Money(amount=Decimal("10"), currency="XYZ")

    def test_empty_currency_raises(self) -> None:
        with pytest.raises(InvalidMoneyError):
            Money(amount=Decimal("10"), currency="")

    def test_invalid_amount_string_raises(self) -> None:
        with pytest.raises(InvalidMoneyError):
            Money.of("not_a_number", "COP")


class TestMoneyAdd:
    def test_same_currency_add(self) -> None:
        a = Money.of("100", "COP")
        b = Money.of("50.50", "COP")
        result = a.add(b)
        assert result.amount == Decimal("150.50")
        assert result.currency == "COP"

    def test_add_returns_new_instance(self) -> None:
        a = Money.of("100", "USD")
        b = Money.of("50", "USD")
        result = a.add(b)
        assert result is not a
        assert result is not b

    def test_different_currencies_raises(self) -> None:
        a = Money.of("100", "COP")
        b = Money.of("50", "USD")
        with pytest.raises(InvalidMoneyError, match="Currency mismatch"):
            a.add(b)

    def test_add_zero(self) -> None:
        a = Money.of("100", "EUR")
        zero = Money.of("0", "EUR")
        assert a.add(zero).amount == Decimal("100")


class TestMoneyImmutability:
    def test_frozen_dataclass(self) -> None:
        m = Money.of("100", "COP")
        with pytest.raises((AttributeError, TypeError)):
            m.amount = Decimal("999")  # type: ignore[misc]

    def test_str_format(self) -> None:
        m = Money.of("100.5", "COP")
        assert "COP" in str(m)
        assert "100.5" in str(m)

    def test_repr_includes_currency(self) -> None:
        m = Money.of("50", "USD")
        assert "USD" in repr(m)
