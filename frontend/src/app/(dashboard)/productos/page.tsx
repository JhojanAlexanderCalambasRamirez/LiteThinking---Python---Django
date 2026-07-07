"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { Button } from "@/components/atoms/Button";
import { Spinner } from "@/components/atoms/Spinner";
import { ProductForm, type ProductoFormValues, type PendingPrecio } from "@/components/organisms/ProductForm";
import { ProductTable, type PrecioFormValues } from "@/components/organisms/ProductTable";
import { productosApi, empresasApi, monedasApi } from "@/lib/api";
import { useToast } from "@/lib/toast";
import { Empresa, Moneda, Producto } from "@/types";

export default function ProductosPage() {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Producto | null>(null);
  const [filterEmpresa, setFilterEmpresa] = useState("");
  const [page, setPage] = useState(1);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: empresas } = useQuery({
    queryKey: ["empresas"],
    queryFn: () => empresasApi.list().then((r) => r.data.results ?? r.data),
  });

  const { data: monedas } = useQuery({
    queryKey: ["monedas"],
    queryFn: () => monedasApi.list().then((r) => r.data.results ?? r.data),
  });

  const { data: productosData, isLoading } = useQuery({
    queryKey: ["productos", filterEmpresa, page],
    queryFn: () => productosApi.list(filterEmpresa || undefined, page).then((r) => r.data),
  });

  const productos: Producto[] = productosData?.results ?? productosData ?? [];
  const totalCount: number = productosData?.count ?? 0;
  const totalPages = Math.ceil(totalCount / 20);
  const hasNext = !!productosData?.next;
  const hasPrev = page > 1;

  const createMutation = useMutation({
    mutationFn: (data: ProductoFormValues & { precios: { moneda_codigo: string; precio: number }[] }) =>
      productosApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["productos"] });
      setShowForm(false);
      setMutationError(null);
      toast.success("Producto creado exitosamente.");
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      setMutationError(detail ? JSON.stringify(detail) : "Error al crear producto.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ProductoFormValues> }) =>
      productosApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["productos"] });
      setEditing(null);
      setMutationError(null);
      toast.success("Producto actualizado.");
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      setMutationError(detail ? JSON.stringify(detail) : "Error al actualizar producto.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => productosApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["productos"] });
      toast.info("Producto desactivado.");
    },
    onError: () => toast.error("No se pudo desactivar el producto."),
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => productosApi.update(id, { activo: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["productos"] });
      toast.success("Producto reactivado.");
    },
  });

  const addPrecioMutation = useMutation({
    mutationFn: ({ productoId, data }: { productoId: string; data: PrecioFormValues }) =>
      productosApi.addPrecio(productoId, { moneda_codigo: data.moneda_codigo, precio: Number(data.precio) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["productos"] }),
  });

  const handleFormSubmit = async (values: ProductoFormValues, precios: PendingPrecio[]) => {
    setMutationError(null);
    if (editing) {
      await updateMutation.mutateAsync({ id: editing.id, data: values });
    } else {
      await createMutation.mutateAsync({
        ...values,
        precios: precios.map((p) => ({ moneda_codigo: p.moneda_codigo, precio: Number(p.precio) })),
      });
    }
  };

  const handleClose = () => {
    setShowForm(false);
    setEditing(null);
    setMutationError(null);
  };

  return (
    <DashboardTemplate
      title="Productos"
      actions={
        <Button onClick={() => { setEditing(null); setShowForm(true); }} size="sm">
          <Plus className="h-4 w-4" /> Nuevo producto
        </Button>
      }
    >
      <div className="space-y-4">
        {/* Filter */}
        <div className="bg-white rounded-xl border p-4">
          <select
            value={filterEmpresa}
            onChange={(e) => { setFilterEmpresa(e.target.value); setPage(1); }}
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
          <ProductForm
            editing={editing}
            empresas={(empresas as Empresa[]) ?? []}
            monedas={(monedas as Moneda[]) ?? []}
            onSubmit={handleFormSubmit}
            onClose={handleClose}
            loading={createMutation.isPending || updateMutation.isPending}
            apiError={mutationError}
          />
        )}

        {/* Table */}
        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : (
          <ProductTable
            productos={productos}
            monedas={(monedas as Moneda[]) ?? []}
            onEdit={(p) => { setShowForm(false); setEditing(p); }}
            onDelete={(id) => deleteMutation.mutate(id)}
            onActivate={(id) => activateMutation.mutate(id)}
            onAddPrecio={async (productoId, data) => {
              await addPrecioMutation.mutateAsync({ productoId, data });
            }}
          />
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between bg-white rounded-xl border px-4 py-3">
            <p className="text-sm text-gray-500">
              Página <span className="font-medium">{page}</span> de{" "}
              <span className="font-medium">{totalPages}</span>{" "}
              &mdash; {totalCount} productos en total
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={!hasPrev}
                onClick={() => setPage((p) => p - 1)}
              >
                ← Anterior
              </Button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
                <button
                  key={n}
                  onClick={() => setPage(n)}
                  className={`w-8 h-8 rounded-md text-sm font-medium transition-colors ${
                    n === page
                      ? "bg-brand-600 text-white"
                      : "text-gray-600 hover:bg-gray-100"
                  }`}
                >
                  {n}
                </button>
              ))}
              <Button
                variant="secondary"
                size="sm"
                disabled={!hasNext}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente →
              </Button>
            </div>
          </div>
        )}
      </div>
    </DashboardTemplate>
  );
}
