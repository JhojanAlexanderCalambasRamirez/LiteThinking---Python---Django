"use client";

import { Check, X, Pencil } from "lucide-react";

import { CurrencyDisplay } from "@/components/molecules/CurrencyDisplay";
import { InventarioItem } from "@/types";

interface InventoryTableProps {
  inventario: InventarioItem[] | undefined;
  isLoading: boolean;
  editingCantidadId: string | null;
  cantidadValue: string;
  savingCantidad: boolean;
  onEditStart: (id: string, cantidad: number) => void;
  onEditSave: (id: string, cantidad: number) => void;
  onEditCancel: () => void;
  onCantidadChange: (value: string) => void;
}

const COLUMNS = ["Código", "Producto", "Empresa", "Características", "Precios", "Cantidad", ""];

export function InventoryTable({
  inventario,
  isLoading,
  editingCantidadId,
  cantidadValue,
  savingCantidad,
  onEditStart,
  onEditSave,
  onEditCancel,
  onCantidadChange,
}: InventoryTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {COLUMNS.map((h) => (
              <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {isLoading ? (
            Array.from({ length: 8 }).map((_, i) => (
              <tr key={i}>
                {[60, 80, 70, 90, 100, 40, 20].map((w, j) => (
                  <td key={j} className="px-4 py-3">
                    <div className="h-4 bg-gray-200 rounded animate-pulse" style={{ width: `${w}%` }} />
                  </td>
                ))}
              </tr>
            ))
          ) : (
            inventario?.map((item) => (
              <tr key={item.id} className={`hover:bg-gray-50 ${item.cantidad === 0 ? "opacity-60" : ""}`}>
                <td className="px-4 py-3 font-mono text-sm">{item.producto_detail.codigo}</td>
                <td className="px-4 py-3 text-sm font-medium">{item.producto_detail.nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{item.empresa_nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                  {item.producto_detail.caracteristicas || "-"}
                </td>
                <td className="px-4 py-3">
                  <CurrencyDisplay precios={item.producto_detail.precios} />
                </td>
                <td className="px-4 py-3 text-sm font-semibold">
                  {editingCantidadId === item.id ? (
                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        min={0}
                        value={cantidadValue}
                        onChange={(e) => onCantidadChange(e.target.value)}
                        className="w-20 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === "Enter") onEditSave(item.id, Number(cantidadValue));
                          if (e.key === "Escape") onEditCancel();
                        }}
                      />
                      <button
                        onClick={() => onEditSave(item.id, Number(cantidadValue))}
                        disabled={savingCantidad}
                        className="text-green-600 hover:text-green-800"
                        aria-label="Guardar cantidad"
                      >
                        <Check className="h-4 w-4" />
                      </button>
                      <button
                        onClick={onEditCancel}
                        className="text-gray-400 hover:text-gray-600"
                        aria-label="Cancelar edición"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : item.cantidad === 0 ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                      Sin stock
                    </span>
                  ) : (
                    item.cantidad
                  )}
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => onEditStart(item.id, item.cantidad)}
                    className="text-gray-400 hover:text-brand-600 transition-colors"
                    aria-label="Editar cantidad"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
      {!isLoading && !inventario?.length && (
        <div className="text-center py-12 text-gray-500">No hay registros en inventario.</div>
      )}
    </div>
  );
}
