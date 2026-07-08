class DomainException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidNITError(DomainException):
    pass


class InvalidEmailError(DomainException):
    pass


class InvalidMoneyError(DomainException):
    pass


class InvalidPasswordHashError(DomainException):
    pass


class EmpresaNotFoundError(DomainException):
    def __init__(self, nit: str) -> None:
        super().__init__(f"Empresa with NIT '{nit}' not found.")


class EmpresaAlreadyExistsError(DomainException):
    def __init__(self, nit: str) -> None:
        super().__init__(f"Empresa with NIT '{nit}' already exists.")


class ProductoNotFoundError(DomainException):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"Producto '{identifier}' not found.")


class ProductoAlreadyExistsError(DomainException):
    def __init__(self, codigo: str, empresa_nit: str) -> None:
        super().__init__(
            f"Producto with code '{codigo}' already exists in empresa '{empresa_nit}'."
        )


class UsuarioNotFoundError(DomainException):
    def __init__(self, email: str) -> None:
        super().__init__(f"Usuario with email '{email}' not found.")


class UsuarioAlreadyExistsError(DomainException):
    def __init__(self, email: str) -> None:
        super().__init__(f"Usuario with email '{email}' already exists.")


class InventarioNotFoundError(DomainException):
    def __init__(self, producto_id: str) -> None:
        super().__init__(f"Inventario entry for producto '{producto_id}' not found.")


class InsufficientStockError(DomainException):
    def __init__(self, producto_id: str, requested: int, available: int) -> None:
        super().__init__(
            f"Insufficient stock for producto '{producto_id}': "
            f"requested {requested}, available {available}."
        )


class UnauthorizedOperationError(DomainException):
    def __init__(self, operation: str) -> None:
        super().__init__(f"Operation '{operation}' requires admin role.")
