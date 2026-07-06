"use client";

import { Fragment, useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X, Pencil, Trash2, PlusCircle, CheckCircle, RotateCcw } from "lucide-react";
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
import { useToast } from "@/lib/toast";
import { Empresa, Moneda, Producto } from "@/types";

// ─── Schemas ────────────────────────────────────────────────────────────────

const productoSchema = z.object({
  codigo: z.string().optional(),
  nombre: z.string().min(2, "Mínimo 2 caracteres"),
  caracteristicas: z.string().optional(),
  empresa_nit: z.string().min(1, "Seleccione una empresa"),
  cantidad_inicial: z.coerce.number().int().min(0, "Mínimo 0").optional(),
});

const precioSchema = z.object({
  moneda_codigo: z.string().min(1, "Seleccione moneda"),
  precio: z.string().min(1, "Ingrese precio").refine((v) => !isNaN(Number(v)) && Number(v) >= 0, "Precio inválido"),
});

type ProductoFormValues = z.infer<typeof productoSchema>;
type PrecioFormValues = z.infer<typeof precioSchema>;

// ─── Page ────────────────────────────────────────────────────────────────────

export default function ProductosPage() {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Producto | null>(null);
  const [filterEmpresa, setFilterEmpresa] = useState("");
  const [page, setPage] = useState(1);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [addingPrecioFor, setAddingPrecioFor] = useState<string | null>(null);
  const [pendingPrecios, setPendingPrecios] = useState<{ moneda_codigo: string; precio: string }[]>([]);
  const [newMoneda, setNewMoneda] = useState("");
  const [newPrecio, setNewPrecio] = useState("");
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

  // ─── Product form ──────────────────────────────────────────────────────────

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProductoFormValues>({ resolver: zodResolver(productoSchema) });

  useEffect(() => {
    if (editing) {
      reset({
        codigo: editing.codigo,
        nombre: editing.nombre,
        caracteristicas: editing.caracteristicas ?? "",
        empresa_nit: editing.empresa_nit,
      });
    } else {
      reset({ codigo: "", nombre: "", caracteristicas: "", empresa_nit: "", cantidad_inicial: 1 });
    }
  }, [editing, reset]);

  const createMutation = useMutation({
    mutationFn: (data: ProductoFormValues) =>
      productosApi.create({
        ...data,
        precios: pendingPrecios.map((p) => ({ moneda_codigo: p.moneda_codigo, precio: Number(p.precio) })),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["productos"] });
      setShowForm(false);
      setMutationError(null);
      setPendingPrecios([]);
      setNewMoneda("");
      setNewPrecio("");
      reset();
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
      setConfirmDeleteId(null);
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

  const onSubmit = async (values: ProductoFormValues) => {
    setMutationError(null);
    if (editing) {
      await updateMutation.mutateAsync({ id: editing.id, data: values });
    } else {
      await createMutation.mutateAsync(values);
    }
  };

  // ─── Price form ────────────────────────────────────────────────────────────

  const {
    register: registerPrecio,
    handleSubmit: handlePrecioSubmit,
    reset: resetPrecio,
    formState: { errors: precioErrors, isSubmitting: precioSubmitting },
  } = useForm<PrecioFormValues>({ resolver: zodResolver(precioSchema) });

  const addPrecioMutation = useMutation({
    mutationFn: ({ productoId, data }: { productoId: string; data: PrecioFormValues }) =>
      productosApi.addPrecio(productoId, { moneda_codigo: data.moneda_codigo, precio: Number(data.precio) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["productos"] });
      setAddingPrecioFor(null);
      resetPrecio();
    },
  });

  const openForm = () => {
    setEditing(null);
    setMutationError(null);
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditing(null);
    setMutationError(null);
    setPendingPrecios([]);
    setNewMoneda("");
    setNewPrecio("");
    reset();
  };

  const addPendingPrecio = () => {
    if (!newMoneda || !newPrecio || isNaN(Number(newPrecio)) || Number(newPrecio) < 0) return;
    if (pendingPrecios.some((p) => p.moneda_codigo === newMoneda)) return;
    setPendingPrecios((prev) => [...prev, { moneda_codigo: newMoneda, precio: newPrecio }]);
    setNewMoneda("");
    setNewPrecio("");
  };

  return (
    <DashboardTemplate
      title="Productos"
      actions={
        <Button onClick={openForm} size="sm">
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
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-semibold text-gray-900">
                {editing ? "Editar producto" : "Nuevo producto"}
              </h2>
              <button onClick={closeForm} className="text-gray-400 hover:text-gray-600" aria-label="Cerrar formulario">
                <X className="h-5 w-5" />
              </button>
            </div>

            {mutationError && (
              <p className="mb-4 text-sm text-red-600 bg-red-50 rounded-md px-3 py-2">{mutationError}</p>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                id="nombre"
                label="Nombre del producto"
                required
                error={errors.nombre?.message}
              >
                <Input
                  id="nombre"
                  placeholder="Ej: Laptop Dell XPS 15"
                  {...register("nombre")}
                  error={!!errors.nombre}
                />
              </FormField>

              <FormField
                id="empresa_nit"
                label="Empresa"
                required
                error={errors.empresa_nit?.message}
              >
                <select
                  {...register("empresa_nit")}
                  disabled={!!editing}
                  className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-500"
                >
                  <option value="">Seleccionar empresa…</option>
                  {(empresas as Empresa[])?.map((e) => (
                    <option key={e.nit} value={e.nit}>{e.nombre}</option>
                  ))}
                </select>
              </FormField>

              {editing && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Código</label>
                  <span className="inline-flex items-center px-3 py-1.5 rounded-md bg-gray-100 font-mono text-sm text-gray-600 border border-gray-200">
                    {editing.codigo}
                  </span>
                </div>
              )}

              <FormField
                id="caracteristicas"
                label="Características"
                error={errors.caracteristicas?.message}
              >
                <Input
                  id="caracteristicas"
                  placeholder="Ej: Intel i7, 16GB RAM, 512GB SSD"
                  {...register("caracteristicas")}
                />
              </FormField>

              {/* Cantidad inicial - only on create */}
              {!editing && (
                <FormField
                  id="cantidad_inicial"
                  label="Cantidad en inventario"
                  error={errors.cantidad_inicial?.message}
                  hint="Unidades disponibles al registrar el producto"
                >
                  <Input
                    id="cantidad_inicial"
                    type="number"
                    min={0}
                    placeholder="1"
                    {...register("cantidad_inicial")}
                  />
                </FormField>
              )}

              {/* Inline prices - only on create */}
              {!editing && (
                <div className="col-span-1 sm:col-span-2 space-y-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Precios <span className="text-gray-400 font-normal">(opcional)</span>
                  </label>

                  {/* Added prices list */}
                  {pendingPrecios.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {pendingPrecios.map((p) => {
                        const m = (monedas as Moneda[])?.find((x) => x.codigo === p.moneda_codigo);
                        return (
                          <span
                            key={p.moneda_codigo}
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 border border-brand-200 text-sm text-brand-700"
                          >
                            {m?.simbolo} {Number(p.precio).toLocaleString("es-CO")} {p.moneda_codigo}
                            <button
                              type="button"
                              onClick={() => setPendingPrecios((prev) => prev.filter((x) => x.moneda_codigo !== p.moneda_codigo))}
                              className="text-brand-400 hover:text-brand-700"
                              aria-label={`Quitar precio ${p.moneda_codigo}`}
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          </span>
                        );
                      })}
                    </div>
                  )}

                  {/* Add price row */}
                  <div className="flex items-end gap-2">
                    <div className="w-44">
                      <select
                        value={newMoneda}
                        onChange={(e) => setNewMoneda(e.target.value)}
                        className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                      >
                        <option value="">Moneda…</option>
                        {(monedas as Moneda[])
                          ?.filter((m) => !pendingPrecios.some((p) => p.moneda_codigo === m.codigo))
                          .map((m) => (
                            <option key={m.codigo} value={m.codigo}>{m.codigo} - {m.nombre}</option>
                          ))}
                      </select>
                    </div>
                    <div className="w-36">
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="0.00"
                        value={newPrecio}
                        onChange={(e) => setNewPrecio(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addPendingPrecio(); } }}
                      />
                    </div>
                    <Button type="button" variant="secondary" size="sm" onClick={addPendingPrecio}>
                      <PlusCircle className="h-4 w-4" /> Agregar
                    </Button>
                  </div>
                </div>
              )}

              <div className="col-span-1 sm:col-span-2 flex gap-3">
                <Button type="submit" loading={isSubmitting}>
                  {editing ? "Guardar cambios" : "Crear producto"}
                </Button>
                <Button type="button" variant="secondary" onClick={closeForm}>
                  Cancelar
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
                {productos?.map((p) => (
                  <Fragment key={p.id}>
                    <tr className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-sm text-gray-700">{p.codigo}</td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{p.nombre}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {p.empresa_nombre ?? p.empresa_nit}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">
                        {p.caracteristicas || <span className="italic text-gray-300">Sin descripción</span>}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <CurrencyDisplay precios={p.precios} />
                          <button
                            onClick={() => setAddingPrecioFor(addingPrecioFor === p.id ? null : p.id)}
                            className="text-brand-500 hover:text-brand-700"
                            aria-label="Agregar precio"
                          >
                            <PlusCircle className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={p.activo ? "success" : "neutral"}>
                          {p.activo ? "Activo" : "Inactivo"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        {confirmDeleteId === p.id ? (
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-600">¿Desactivar?</span>
                            <button
                              onClick={() => deleteMutation.mutate(p.id)}
                              className="text-xs text-red-600 font-medium hover:underline"
                            >
                              Sí
                            </button>
                            <button
                              onClick={() => setConfirmDeleteId(null)}
                              className="text-xs text-gray-500 hover:underline"
                            >
                              No
                            </button>
                          </div>
                        ) : p.activo ? (
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => { setShowForm(false); setEditing(p); }}
                              aria-label={`Editar ${p.nombre}`}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="danger"
                              size="sm"
                              onClick={() => setConfirmDeleteId(p.id)}
                              aria-label={`Desactivar ${p.nombre}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        ) : (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => activateMutation.mutate(p.id)}
                            title="Reactivar producto"
                          >
                            <RotateCcw className="h-4 w-4" /> Activar
                          </Button>
                        )}
                      </td>
                    </tr>

                    {/* Inline add-precio row */}
                    {addingPrecioFor === p.id && (
                      <tr className="bg-brand-50">
                        <td colSpan={7} className="px-4 py-3">
                          <form
                            onSubmit={handlePrecioSubmit((data) =>
                              addPrecioMutation.mutate({ productoId: p.id, data })
                            )}
                            className="flex items-end gap-3"
                          >
                            <div className="w-40">
                              <label className="block text-xs font-medium text-gray-600 mb-1">Moneda</label>
                              <select
                                {...registerPrecio("moneda_codigo")}
                                className="block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm"
                              >
                                <option value="">Seleccionar…</option>
                                {(monedas as Moneda[])?.map((m) => (
                                  <option key={m.codigo} value={m.codigo}>{m.codigo} - {m.nombre}</option>
                                ))}
                              </select>
                              {precioErrors.moneda_codigo && (
                                <p className="text-xs text-red-500 mt-0.5">{precioErrors.moneda_codigo.message}</p>
                              )}
                            </div>
                            <div className="w-36">
                              <label className="block text-xs font-medium text-gray-600 mb-1">Precio</label>
                              <Input
                                {...registerPrecio("precio")}
                                type="number"
                                step="0.01"
                                placeholder="0.00"
                                error={!!precioErrors.precio}
                              />
                              {precioErrors.precio && (
                                <p className="text-xs text-red-500 mt-0.5">{precioErrors.precio.message}</p>
                              )}
                            </div>
                            <Button type="submit" size="sm" loading={precioSubmitting}>
                              <CheckCircle className="h-4 w-4" /> Agregar
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              onClick={() => { setAddingPrecioFor(null); resetPrecio(); }}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </form>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
            {!productos?.length && (
              <div className="text-center py-12 text-gray-400">No hay productos registrados.</div>
            )}
          </div>
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
