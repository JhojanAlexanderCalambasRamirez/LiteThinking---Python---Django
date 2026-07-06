"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { CompanyTable } from "@/components/organisms/CompanyTable";
import { CompanyForm, EmpresaFormValues } from "@/components/organisms/CompanyForm";
import { Button } from "@/components/atoms/Button";
import { Spinner } from "@/components/atoms/Spinner";
import { empresasApi } from "@/lib/api";
import { isAdmin } from "@/lib/auth";
import { Empresa } from "@/types";

export default function EmpresasPage() {
  const [showForm, setShowForm] = useState(false);
  const [editingEmpresa, setEditingEmpresa] = useState<Empresa | null>(null);
  const queryClient = useQueryClient();
  const admin = isAdmin();

  const { data, isLoading } = useQuery({
    queryKey: ["empresas"],
    queryFn: () => empresasApi.list().then((r) => r.data.results ?? r.data),
  });

  const createMutation = useMutation({
    mutationFn: (values: EmpresaFormValues) => empresasApi.create(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["empresas"] });
      setShowForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ nit, data }: { nit: string; data: Partial<EmpresaFormValues> }) =>
      empresasApi.update(nit, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["empresas"] });
      setEditingEmpresa(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (nit: string) => empresasApi.delete(nit),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["empresas"] }),
  });

  const handleEdit = (empresa: Empresa) => setEditingEmpresa(empresa);
  const handleDelete = (nit: string) => {
    if (confirm("¿Desactivar esta empresa?")) deleteMutation.mutate(nit);
  };

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
            <button onClick={() => { setShowForm(false); setEditingEmpresa(null); }}>
              <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            </button>
          </div>
          <CompanyForm
            defaultValues={editingEmpresa ?? undefined}
            isEditing={!!editingEmpresa}
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
          onDelete={handleDelete}
        />
      )}
    </DashboardTemplate>
  );
}
