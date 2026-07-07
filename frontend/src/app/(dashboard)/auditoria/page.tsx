"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shield, CheckCircle2, Clock } from "lucide-react";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { blockchainApi } from "@/lib/api";
import { BlockchainLog } from "@/types";

const ENTITY_FILTERS = [
  { label: "Todos", value: "" },
  { label: "Inventario", value: "inventario" },
  { label: "Empresa", value: "empresa" },
  { label: "Producto", value: "producto" },
];

const ACTION_COLORS: Record<string, string> = {
  CREATE: "bg-green-100 text-green-700",
  UPDATE: "bg-blue-100 text-blue-700",
  DELETE: "bg-red-100 text-red-700",
};

export default function AuditoriaPage() {
  const [entityFilter, setEntityFilter] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["blockchain-log", entityFilter],
    queryFn: () =>
      blockchainApi.getLogs(entityFilter || undefined, 100).then((r) => r.data.logs as BlockchainLog[]),
    refetchInterval: 30_000,
  });

  return (
    <DashboardTemplate title="Auditoría Blockchain">
      <div className="space-y-6">
        {/* Info banner */}
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex gap-3">
          <Shield className="h-5 w-5 text-purple-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-purple-800">
            <strong>Registro inmutable de operaciones críticas.</strong> Cada operación genera un hash
            SHA-256 del payload. Cuando la red Polygon está disponible, el hash se ancla en cadena
            (tx_hash). En modo local, el hash garantiza integridad sin costo de red.
          </div>
        </div>

        {/* Filter */}
        <div className="flex gap-2">
          {ENTITY_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setEntityFilter(f.value)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                entityFilter === f.value
                  ? "bg-brand-600 text-white"
                  : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {["Entidad", "ID", "Acción", "Hash SHA-256", "On-chain", "Red", "Fecha"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}>
                    {[60, 80, 40, 100, 30, 50, 70].map((w, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-gray-200 rounded animate-pulse" style={{ width: `${w}%` }} />
                      </td>
                    ))}
                  </tr>
                ))
              ) : isError ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-red-500 text-sm">
                    No se pudo conectar con el servicio de auditoría.
                  </td>
                </tr>
              ) : data?.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-400 text-sm">
                    No hay registros de auditoría aún.
                  </td>
                </tr>
              ) : (
                data?.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="text-xs font-medium text-gray-700 bg-gray-100 px-2 py-0.5 rounded">
                        {log.entity_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500 max-w-[120px] truncate">
                      {log.entity_id}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${ACTION_COLORS[log.accion] ?? "bg-gray-100 text-gray-700"}`}>
                        {log.accion}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500 max-w-[160px] truncate" title={log.data_hash}>
                      {log.data_hash.slice(0, 16)}…
                    </td>
                    <td className="px-4 py-3">
                      {log.on_chain ? (
                        <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Anclado
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-gray-400">
                          <Clock className="h-3.5 w-3.5" />
                          Local
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {log.network ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString("es-CO", {
                        dateStyle: "short",
                        timeStyle: "short",
                      })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </DashboardTemplate>
  );
}
