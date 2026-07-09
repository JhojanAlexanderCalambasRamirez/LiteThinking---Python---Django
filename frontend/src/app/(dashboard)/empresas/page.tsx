"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { CompanyTable } from "@/components/organisms/CompanyTable";
import { CompanyForm, EmpresaFormValues } from "@/components/organisms/CompanyForm";
import { Button } from "@/components/atoms/Button";
import { Spinner } from "@/components/atoms/Spinner";
import { empresasApi } from "@/lib/api";
import { isAdmin } from "@/lib/auth";
import { useToast } from "@/lib/toast";
import { Empresa } from "@/types";

export default function EmpresasPage() {
  const [showForm, setShowForm] = useState(false);
  const [editingEmpresa, setEditingEmpresa] = useState<Empresa | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [admin, setAdmin] = useState(false);
  const queryClient = useQueryClient();
  const toast = useToast();

  useEffect(() => { setAdmin(isAdmin()); }, []);

  const { data, isLoading } = useQuery({
    queryKey: ["empresas"],
    queryFn: () => empresasApi.list().then((r) => r.data.results ?? r.data),
  });

  const createMutation = useMutation({
    mutationFn: (values: EmpresaFormValues) => empresasApi.create(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["empresas"] });
      setShowForm(false);
      setFormError(null);
      toast.success("Empresa registrada exitosamente.");
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const msg = detail
        ? Object.values(detail).flat().map(String).join(" ")
        : "Error al crear la empresa.";
      setFormError(msg);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ nit, data }: { nit: string; data: Partial<EmpresaFormValues> }) =>
      empresasApi.update(nit, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["empresas"] });
      setEditingEmpresa(null);
      setFormError(null);
      toast.success("Empresa actualizada exitosamente.");
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const msg = detail
        ? Object.values(detail).flat().map(String).join(" ")
        : "Error al actualizar la empresa.";
      setFormError(msg);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (nit: string) => empresasApi.delete(nit),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["empresas"] });
      toast.info("Empresa desactivada.");
    },
    onError: () => toast.error("No se pudo desactivar la empresa."),
  });

  const handleEdit = (empresa: Empresa) => { setEditingEmpresa(empresa); setFormError(null); };

  return (
    <DashboardTemplate
      title="Empresas"
      actions={
        admin ? (
          <Button onClick={() => setShowForm(true)} size="sm">
            <Plus className="h-4 w-4" /> Nueva empresa
          </Button>
        ) : undefined
      }
    >
      {(showForm || editingEmpresa) && (
        <div className="mb-6 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-semibold text-gray-900">
              {editingEmpresa ? "Editar empresa" : "Registrar empresa"}
            </h2>
            <button onClick={() => { setShowForm(false); setEditingEmpresa(null); setFormError(null); }} aria-label="Cerrar formulario">
              <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            </button>
          </div>
          <CompanyForm
            key={editingEmpresa?.nit ?? "new"}
            defaultValues={editingEmpresa ?? undefined}
            isEditing={!!editingEmpresa}
            apiError={formError}
            onSubmit={async (values) => {
              if (editingEmpresa) {
                await updateMutation.mutateAsync({ nit: editingEmpresa.nit, data: values });
              } else {
                await createMutation.mutateAsync(values);
              }
            }}
          />
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : (
        <CompanyTable
          empresas={data ?? []}
          isAdmin={admin}
          onEdit={handleEdit}
          onDelete={(nit) => deleteMutation.mutate(nit)}
        />
      )}
    </DashboardTemplate>
  );
}
