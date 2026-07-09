"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { X, PlusCircle } from "lucide-react";

import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { Label } from "@/components/atoms/Label";
import { FormField } from "@/components/molecules/FormField";
import { Empresa, Moneda, Producto } from "@/types";

const productoSchema = z.object({
  codigo: z.string().optional(),
  nombre: z.string().min(2, "Mínimo 2 caracteres"),
  caracteristicas: z.string().optional(),
  empresa_nit: z.string().min(1, "Seleccione una empresa"),
  cantidad_inicial: z.coerce.number().int().min(0, "Mínimo 0").optional(),
});

export type ProductoFormValues = z.infer<typeof productoSchema>;
export type PendingPrecio = { moneda_codigo: string; precio: string };

interface ProductFormProps {
  editing?: Producto | null;
  empresas: Empresa[];
  monedas: Moneda[];
  onSubmit: (data: ProductoFormValues, precios: PendingPrecio[]) => Promise<void>;
  onClose: () => void;
  loading?: boolean;
  apiError?: string | null;
}

export function ProductForm({
  editing,
  empresas,
  monedas,
  onSubmit,
  onClose,
  loading,
  apiError,
}: ProductFormProps) {
  const [pendingPrecios, setPendingPrecios] = useState<PendingPrecio[]>([]);
  const [newMoneda, setNewMoneda] = useState("");
  const [newPrecio, setNewPrecio] = useState("");

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
    setPendingPrecios([]);
    setNewMoneda("");
    setNewPrecio("");
  }, [editing, reset]);

  const addPendingPrecio = () => {
    if (!newMoneda || !newPrecio || isNaN(Number(newPrecio)) || Number(newPrecio) < 0) return;
    if (pendingPrecios.some((p) => p.moneda_codigo === newMoneda)) return;
    setPendingPrecios((prev) => [...prev, { moneda_codigo: newMoneda, precio: newPrecio }]);
    setNewMoneda("");
    setNewPrecio("");
  };

  return (
    <div className="bg-white rounded-xl border p-6 shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="font-semibold text-gray-900">
          {editing ? "Editar producto" : "Nuevo producto"}
        </h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
          aria-label="Cerrar formulario"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {apiError && (
        <p className="mb-4 text-sm text-red-600 bg-red-50 rounded-md px-3 py-2">{apiError}</p>
      )}

      <form
        onSubmit={handleSubmit((values) => onSubmit(values, pendingPrecios))}
        className="grid grid-cols-1 sm:grid-cols-2 gap-4"
      >
        <FormField id="nombre" label="Nombre del producto" required error={errors.nombre?.message}>
          <Input
            id="nombre"
            placeholder="Ej: Laptop Dell XPS 15"
            {...register("nombre")}
            error={!!errors.nombre}
          />
        </FormField>

        <FormField id="empresa_nit" label="Empresa" required error={errors.empresa_nit?.message}>
          <select
            {...register("empresa_nit")}
            disabled={!!editing}
            className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-500"
          >
            <option value="">Seleccionar empresa…</option>
            {empresas.map((e) => (
              <option key={e.nit} value={e.nit}>
                {e.nombre}
              </option>
            ))}
          </select>
        </FormField>

        {editing && (
          <div>
            <Label className="mb-1">Código</Label>
            <span className="inline-flex items-center px-3 py-1.5 rounded-md bg-gray-100 font-mono text-sm text-gray-600 border border-gray-200">
              {editing.codigo}
            </span>
          </div>
        )}

        <FormField id="caracteristicas" label="Características" error={errors.caracteristicas?.message}>
          <Input
            id="caracteristicas"
            placeholder="Ej: Intel i7, 16GB RAM, 512GB SSD"
            {...register("caracteristicas")}
          />
        </FormField>

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

        {!editing && (
          <div className="col-span-1 sm:col-span-2 space-y-3">
            <Label>
              Precios <span className="text-gray-400 font-normal">(opcional)</span>
            </Label>

            {pendingPrecios.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {pendingPrecios.map((p) => {
                  const m = monedas.find((x) => x.codigo === p.moneda_codigo);
                  return (
                    <span
                      key={p.moneda_codigo}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 border border-brand-200 text-sm text-brand-700"
                    >
                      {m?.simbolo} {Number(p.precio).toLocaleString("es-CO")} {p.moneda_codigo}
                      <button
                        type="button"
                        onClick={() =>
                          setPendingPrecios((prev) =>
                            prev.filter((x) => x.moneda_codigo !== p.moneda_codigo)
                          )
                        }
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

            <div className="flex items-end gap-2">
              <div className="w-44">
                <select
                  value={newMoneda}
                  onChange={(e) => setNewMoneda(e.target.value)}
                  className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">Moneda…</option>
                  {monedas
                    .filter((m) => !pendingPrecios.some((p) => p.moneda_codigo === m.codigo))
                    .map((m) => (
                      <option key={m.codigo} value={m.codigo}>
                        {m.codigo} - {m.nombre}
                      </option>
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
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addPendingPrecio();
                    }
                  }}
                />
              </div>
              <Button type="button" variant="secondary" size="sm" onClick={addPendingPrecio}>
                <PlusCircle className="h-4 w-4" /> Agregar
              </Button>
            </div>
          </div>
        )}

        <div className="col-span-1 sm:col-span-2 flex gap-3">
          <Button type="submit" loading={isSubmitting || loading}>
            {editing ? "Guardar cambios" : "Crear producto"}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </div>
  );
}
