class DomainException(Exception):
    """Base for all domain exceptions."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# --- Value Object exceptions ---

class InvalidNITError(DomainException):
    """NIT does not match Colombian format (6-10 digits, optional '-' + check digit)."""


class InvalidEmailError(DomainException):
    """Email address has invalid format."""


class InvalidMoneyError(DomainException):
    """Money amount is negative or currency code is invalid."""


class InvalidPasswordHashError(DomainException):
    """Password hash does not match expected bcrypt/argon2 format."""


# --- Empresa exceptions ---

class EmpresaNotFoundError(DomainException):
    def __init__(self, nit: str) -> None:
        super().__init__(f"Empresa with NIT '{nit}' not found.")


class EmpresaAlreadyExistsError(DomainException):
    def __init__(self, nit: str) -> None:
        super().__init__(f"Empresa with NIT '{nit}' already exists.")


# --- Producto exceptions ---

class ProductoNotFoundError(DomainException):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"Producto '{identifier}' not found.")


class ProductoAlreadyExistsError(DomainException):
    def __init__(self, codigo: str, empresa_nit: str) -> None:
        super().__init__(
            f"Producto with code '{codigo}' already exists in empresa '{empresa_nit}'."
        )


# --- Usuario exceptions ---

class UsuarioNotFoundError(DomainException):
    def __init__(self, email: str) -> None:
        super().__init__(f"Usuario with email '{email}' not found.")


class UsuarioAlreadyExistsError(DomainException):
    def __init__(self, email: str) -> None:
        super().__init__(f"Usuario with email '{email}' already exists.")


# --- Inventario exceptions ---

class InventarioNotFoundError(DomainException):
    def __init__(self, producto_id: str) -> None:
        super().__init__(f"Inventario entry for producto '{producto_id}' not found.")


class InsufficientStockError(DomainException):
    def __init__(self, producto_id: str, requested: int, available: int) -> None:
        super().__init__(
            f"Insufficient stock for producto '{producto_id}': "
            f"requested {requested}, available {available}."
        )


# --- Authorization exceptions ---

class UnauthorizedOperationError(DomainException):
    def __init__(self, operation: str) -> None:
        super().__init__(f"Operation '{operation}' requires admin role.")
