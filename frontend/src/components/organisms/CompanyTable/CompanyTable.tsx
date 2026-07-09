"use client";

import { useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";
import { Empresa } from "@/types";

interface CompanyTableProps {
  readonly empresas: Empresa[];
  readonly isAdmin: boolean;
  readonly onEdit?: (empresa: Empresa) => void;
  readonly onDelete?: (nit: string) => void;
}

export function CompanyTable({ empresas, isAdmin, onEdit, onDelete }: CompanyTableProps) {
  const [confirmDeleteNit, setConfirmDeleteNit] = useState<string | null>(null);

  if (!empresas.length) {
    return (
      <div className="text-center py-12 text-gray-500">
        No hay empresas registradas.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {["NIT", "Nombre", "Dirección", "Teléfono", "Estado", ...(isAdmin ? ["Acciones"] : [])].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {empresas.map((empresa) => (
            <tr key={empresa.nit} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 font-mono text-sm text-gray-900">{empresa.nit}</td>
              <td className="px-4 py-3 text-sm font-medium text-gray-900">{empresa.nombre}</td>
              <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{empresa.direccion}</td>
              <td className="px-4 py-3 text-sm text-gray-600">{empresa.telefono}</td>
              <td className="px-4 py-3">
                <Badge variant={empresa.activo ? "success" : "neutral"}>
                  {empresa.activo ? "Activo" : "Inactivo"}
                </Badge>
              </td>
              {isAdmin && (
                <td className="px-4 py-3">
                  {confirmDeleteNit === empresa.nit ? (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-600">¿Desactivar?</span>
                      <button
                        onClick={() => { onDelete?.(empresa.nit); setConfirmDeleteNit(null); }}
                        className="text-xs text-red-600 font-medium hover:underline"
                      >
                        Sí
                      </button>
                      <button
                        onClick={() => setConfirmDeleteNit(null)}
                        className="text-xs text-gray-500 hover:underline"
                      >
                        No
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => onEdit?.(empresa)} aria-label={`Editar ${empresa.nombre}`}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button variant="danger" size="sm" onClick={() => setConfirmDeleteNit(empresa.nit)} aria-label={`Eliminar ${empresa.nombre}`}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
