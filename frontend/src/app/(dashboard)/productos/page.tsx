"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X, Pencil, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { Spinner } from "@/components/atoms/Spinner";
import { Badge } from "@/components/atoms/Badge";
import { FormField } from "@/components/molecules/FormField";
import { CurrencyDisplay } from "@/components/molecules/CurrencyDisplay";
import { productosApi, empresasApi, monedasApi } from "@/lib/api";
import { Empresa, Moneda, Producto } from "@/types";

const productoSchema = z.object({
  codigo: z.string().min(1, "Código requerido"),
  nombre: z.string().min(2, "Mínimo 2 caracteres"),
  caracteristicas: z.string().optional(),
  empresa_nit: z.string().min(1, "Seleccione una empresa"),
});

type ProductoFormValues = z.infer<typeof productoSchema>;

export default function ProductosPage() {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Producto | null>(null);
  const [filterEmpresa, setFilterEmpresa] = useState("");
  const queryClient = useQueryClient();

  const { data: empresas } = useQuery({
    queryKey: ["empresas"],
    queryFn: () => empresasApi.list().then((r) => r.data.results ?? r.data),
  });

  const { data: monedas } = useQuery({
    queryKey: ["monedas"],
    queryFn: () => monedasApi.list().then((r) => r.data.results ?? r.data),
  });

  const { data: productos, isLoading } = useQuery({
    queryKey: ["productos", filterEmpresa],
    queryFn: () =>
      productosApi
        .list(filterEmpresa || undefined)
        .then((r) => r.data.results ?? r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: ProductoFormValues) => productosApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["productos"] });
      setShowForm(false);
      reset();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ProductoFormValues> }) =>
      productosApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["productos"] });
      setEditing(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => productosApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["productos"] }),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProductoFormValues>({
    resolver: zodResolver(productoSchema),
    defaultValues: editing ?? undefined,
  });

  const onSubmit = async (values: ProductoFormValues) => {
    if (editing) {
      await updateMutation.mutateAsync({ id: editing.id, data: values });
    } else {
      await createMutation.mutateAsync(values);
    }
  };

  return (
    <DashboardTemplate
      title="Productos"
      actions={
        <Button onClick={() => { setShowForm(true); setEditing(null); }} size="sm">
          <Plus className="h-4 w-4" /> Nuevo producto
        </Button>
      }
    >
      <div className="space-y-4">
        {/* Filter */}
        <div className="bg-white rounded-xl border p-4">
          <select
            value={filterEmpresa}
            onChange={(e) => setFilterEmpresa(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">Todas las empresas</option>
            {(empresas as Empresa[])?.map((e) => (
              <option key={e.nit} value={e.nit}>{e.nombre}</option>
            ))}
          </select>
        </div>

        {/* Form */}
        {(showForm || editing) && (
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-semibold">{editing ? "Editar producto" : "Nuevo producto"}</h2>
              <button onClick={() => { setShowForm(false); setEditing(null); reset(); }}>
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 gap-4">
              <FormField id="codigo" label="Código" required error={errors.codigo?.message}>
                <Input id="codigo" {...register("codigo")} error={!!errors.codigo} />
              </FormField>
              <FormField id="nombre" label="Nombre" required error={errors.nombre?.message}>
                <Input id="nombre" {...register("nombre")} error={!!errors.nombre} />
              </FormField>
              <FormField id="empresa_nit" label="Empresa" required error={errors.empresa_nit?.message} >
                <select
                  {...register("empresa_nit")}
                  className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">Seleccionar…</option>
                  {(empresas as Empresa[])?.map((e) => (
                    <option key={e.nit} value={e.nit}>{e.nombre}</option>
                  ))}
                </select>
              </FormField>
              <FormField id="caracteristicas" label="Características">
                <Input id="caracteristicas" {...register("caracteristicas")} />
              </FormField>
              <div className="col-span-2">
                <Button type="submit" loading={isSubmitting}>
                  {editing ? "Actualizar" : "Crear producto"}
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Table */}
        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {["Código", "Nombre", "Empresa", "Características", "Precios", "Estado", "Acciones"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {(productos as Producto[])?.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-sm">{p.codigo}</td>
                    <td className="px-4 py-3 text-sm font-medium">{p.nombre}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{p.empresa_nit}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{p.caracteristicas || "-"}</td>
                    <td className="px-4 py-3"><CurrencyDisplay precios={p.precios} /></td>
                    <td className="px-4 py-3">
                      <Badge variant={p.activo ? "success" : "neutral"}>{p.activo ? "Activo" : "Inactivo"}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm" onClick={() => { setEditing(p); setShowForm(false); }}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="danger" size="sm" onClick={() => {
                          if (confirm("¿Desactivar producto?")) deleteMutation.mutate(p.id);
                        }}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!productos?.length && (
              <div className="text-center py-12 text-gray-500">No hay productos registrados.</div>
            )}
          </div>
        )}
      </div>
    </DashboardTemplate>
  );
}
