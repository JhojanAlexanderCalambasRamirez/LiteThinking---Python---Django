"use client";

import { Fragment, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Pencil, Trash2, PlusCircle, CheckCircle, X, RotateCcw } from "lucide-react";

import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { Badge } from "@/components/atoms/Badge";
import { CurrencyDisplay } from "@/components/molecules/CurrencyDisplay";
import { Moneda, Producto } from "@/types";

const precioSchema = z.object({
  moneda_codigo: z.string().min(1, "Seleccione moneda"),
  precio: z
    .string()
    .min(1, "Ingrese precio")
    .refine((v) => !isNaN(Number(v)) && Number(v) >= 0, "Precio inválido"),
});

export type PrecioFormValues = z.infer<typeof precioSchema>;

interface ProductTableProps {
  productos: Producto[];
  monedas: Moneda[];
  onEdit: (producto: Producto) => void;
  onDelete: (id: string) => void;
  onActivate: (id: string) => void;
  onAddPrecio: (productoId: string, data: PrecioFormValues) => Promise<void>;
}

export function ProductTable({
  productos,
  monedas,
  onEdit,
  onDelete,
  onActivate,
  onAddPrecio,
}: ProductTableProps) {
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [addingPrecioFor, setAddingPrecioFor] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PrecioFormValues>({ resolver: zodResolver(precioSchema) });

  if (!productos?.length) {
    return (
      <div className="text-center py-12 text-gray-400">No hay productos registrados.</div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {["Código", "Nombre", "Empresa", "Características", "Precios", "Estado", "Acciones"].map(
              (h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase"
                >
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {productos.map((p) => (
            <Fragment key={p.id}>
              <tr className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-sm text-gray-700">{p.codigo}</td>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{p.nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{p.empresa_nombre ?? p.empresa_nit}</td>
                <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">
                  {p.caracteristicas || (
                    <span className="italic text-gray-300">Sin descripción</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <CurrencyDisplay precios={p.precios} />
                    <button
                      onClick={() =>
                        setAddingPrecioFor(addingPrecioFor === p.id ? null : p.id)
                      }
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
                        onClick={() => {
                          onDelete(p.id);
                          setConfirmDeleteId(null);
                        }}
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
                        onClick={() => onEdit(p)}
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
                      onClick={() => onActivate(p.id)}
                      title="Reactivar producto"
                    >
                      <RotateCcw className="h-4 w-4" /> Activar
                    </Button>
                  )}
                </td>
              </tr>

              {addingPrecioFor === p.id && (
                <tr className="bg-brand-50">
                  <td colSpan={7} className="px-4 py-3">
                    <form
                      onSubmit={handleSubmit(async (data) => {
                        await onAddPrecio(p.id, data);
                        setAddingPrecioFor(null);
                        reset();
                      })}
                      className="flex items-end gap-3"
                    >
                      <div className="w-40">
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Moneda
                        </label>
                        <select
                          {...register("moneda_codigo")}
                          className="block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm"
                        >
                          <option value="">Seleccionar…</option>
                          {monedas.map((m) => (
                            <option key={m.codigo} value={m.codigo}>
                              {m.codigo} - {m.nombre}
                            </option>
                          ))}
                        </select>
                        {errors.moneda_codigo && (
                          <p className="text-xs text-red-500 mt-0.5">
                            {errors.moneda_codigo.message}
                          </p>
                        )}
                      </div>
                      <div className="w-36">
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Precio
                        </label>
                        <Input
                          {...register("precio")}
                          type="number"
                          step="0.01"
                          placeholder="0.00"
                          error={!!errors.precio}
                        />
                        {errors.precio && (
                          <p className="text-xs text-red-500 mt-0.5">{errors.precio.message}</p>
                        )}
                      </div>
                      <Button type="submit" size="sm" loading={isSubmitting}>
                        <CheckCircle className="h-4 w-4" /> Agregar
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setAddingPrecioFor(null);
                          reset();
                        }}
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
    </div>
  );
}
