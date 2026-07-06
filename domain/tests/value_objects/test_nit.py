import pytest

from litethinking_domain.exceptions import InvalidNITError
from litethinking_domain.value_objects import NIT


class TestNITValidFormats:
    def test_6_digits(self) -> None:
        assert str(NIT("123456")) == "123456"

    def test_10_digits(self) -> None:
        assert str(NIT("9001234567")) == "9001234567"

    def test_with_check_digit(self) -> None:
        assert str(NIT("900123456-7")) == "900123456-7"

    def test_minimum_6_digits(self) -> None:
        NIT("123456")

    def test_maximum_10_digits_no_dash(self) -> None:
        NIT("1234567890")

    def test_maximum_with_check_digit(self) -> None:
        NIT("1234567890-9")


class TestNITInvalidFormats:
    def test_too_short_raises(self) -> None:
        with pytest.raises(InvalidNITError):
            NIT("12345")

    def test_too_long_raises(self) -> None:
        with pytest.raises(InvalidNITError):
            NIT("12345678901")

    def test_letters_raises(self) -> None:
        with pytest.raises(InvalidNITError):
            NIT("abc-xyz")

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidNITError):
            NIT("")

    def test_dash_only_raises(self) -> None:
        with pytest.raises(InvalidNITError):
            NIT("-7")

    def test_wrong_dash_position_raises(self) -> None:
        with pytest.raises(InvalidNITError):
            NIT("90012-456-7")

    def test_multiple_check_digits_raises(self) -> None:
        with pytest.raises(InvalidNITError):
            NIT("900123456-77")

    def test_spaces_raises(self) -> None:
        with pytest.raises(InvalidNITError):
            NIT("900 123456")


class TestNITEquality:
    def test_same_value_equal(self) -> None:
        assert NIT("900123456-7") == NIT("900123456-7")

    def test_different_values_not_equal(self) -> None:
        assert NIT("900123456-7") != NIT("900123456-8")

    def test_with_and_without_check_digit_not_equal(self) -> None:
        assert NIT("900123456") != NIT("900123456-7")


class TestNITImmutability:
    def test_frozen_dataclass(self) -> None:
        nit = NIT("900123456-7")
        with pytest.raises((AttributeError, TypeError)):
            nit.valor = "other"  # type: ignore[misc]

    def test_str_representation(self) -> None:
        nit = NIT("900123456-7")
        assert str(nit) == "900123456-7"

    def test_from_string_factory(self) -> None:
        nit = NIT.from_string("  900123456-7  ")
        assert str(nit) == "900123456-7"


class TestNITErrorMessage:
    def test_error_contains_invalid_value(self) -> None:
        with pytest.raises(InvalidNITError, match="abc"):
            NIT("abc")
