from __future__ import annotations

from litethinking_domain.entities import Empresa
from litethinking_domain.repositories import EmpresaRepository
from litethinking_domain.value_objects import NIT

from .models import EmpresaModel


class DjangoEmpresaRepository(EmpresaRepository):
    """
    Django ORM implementation of EmpresaRepository port.
    Translates between domain entities and Django ORM models.
    """

    def find_by_nit(self, nit: NIT) -> Empresa | None:
        try:
            model = EmpresaModel.objects.get(nit=str(nit))
            return model.to_domain()
        except EmpresaModel.DoesNotExist:
            return None

    def find_all(self, include_inactive: bool = False) -> list[Empresa]:
        qs = EmpresaModel.objects.all()
        if not include_inactive:
            qs = qs.filter(activo=True)
        return [m.to_domain() for m in qs]

    def exists_by_nit(self, nit: NIT) -> bool:
        return EmpresaModel.objects.filter(nit=str(nit)).exists()

    def save(self, empresa: Empresa) -> Empresa:
        model, _ = EmpresaModel.objects.update_or_create(
            nit=str(empresa.nit),
            defaults={
                "nombre": empresa.nombre,
                "direccion": empresa.direccion,
                "telefono": empresa.telefono,
                "activo": empresa.activo,
            },
        )
        return model.to_domain()

    def delete(self, nit: NIT) -> None:
        EmpresaModel.objects.filter(nit=str(nit)).update(activo=False)
