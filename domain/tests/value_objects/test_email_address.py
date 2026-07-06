import pytest

from litethinking_domain.exceptions import InvalidEmailError
from litethinking_domain.value_objects import EmailAddress


class TestEmailAddressValidFormats:
    def test_simple_email(self) -> None:
        e = EmailAddress("user@example.com")
        assert str(e) == "user@example.com"

    def test_subdomain(self) -> None:
        EmailAddress("user@mail.example.com")

    def test_plus_tag(self) -> None:
        EmailAddress("user+tag@example.com")

    def test_dots_in_local(self) -> None:
        EmailAddress("first.last@example.com")

    def test_digits_in_local(self) -> None:
        EmailAddress("user123@example.com")

    def test_hyphen_in_domain(self) -> None:
        EmailAddress("user@my-domain.com")


class TestEmailAddressNormalization:
    def test_uppercased_normalized_to_lower(self) -> None:
        e = EmailAddress("USER@EXAMPLE.COM")
        assert str(e) == "user@example.com"

    def test_mixed_case_normalized(self) -> None:
        e = EmailAddress("John.DOE@Company.ORG")
        assert str(e) == "john.doe@company.org"

    def test_leading_trailing_spaces_stripped(self) -> None:
        e = EmailAddress.from_string("  user@example.com  ")
        assert str(e) == "user@example.com"

    def test_equality_after_normalization(self) -> None:
        assert EmailAddress("USER@EXAMPLE.COM") == EmailAddress("user@example.com")


class TestEmailAddressInvalidFormats:
    def test_no_at_sign_raises(self) -> None:
        with pytest.raises(InvalidEmailError):
            EmailAddress("notanemail")

    def test_no_domain_raises(self) -> None:
        with pytest.raises(InvalidEmailError):
            EmailAddress("user@")

    def test_no_local_raises(self) -> None:
        with pytest.raises(InvalidEmailError):
            EmailAddress("@domain.com")

    def test_no_tld_raises(self) -> None:
        with pytest.raises(InvalidEmailError):
            EmailAddress("user@domain")

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidEmailError):
            EmailAddress("")

    def test_spaces_in_middle_raises(self) -> None:
        with pytest.raises(InvalidEmailError):
            EmailAddress("user @example.com")


class TestEmailAddressImmutability:
    def test_frozen_dataclass(self) -> None:
        e = EmailAddress("user@example.com")
        with pytest.raises((AttributeError, TypeError)):
            e.valor = "other@example.com"  # type: ignore[misc]

    def test_str_returns_valor(self) -> None:
        e = EmailAddress("user@example.com")
        assert str(e) == e.valor
