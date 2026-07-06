"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Download, Mail, Pencil, Check, X } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { FormField } from "@/components/molecules/FormField";
import { CurrencyDisplay } from "@/components/molecules/CurrencyDisplay";
import { inventarioApi, empresasApi } from "@/lib/api";
import { useToast } from "@/lib/toast";
import { InventarioItem } from "@/types";

const emailSchema = z.object({
  recipient_email: z.string().email("Email inválido"),
});

type EmailFormValues = z.infer<typeof emailSchema>;

export default function InventarioPage() {
  const queryClient = useQueryClient();
  const [selectedEmpresa, setSelectedEmpresa] = useState<string>("");
  const [emailSent, setEmailSent] = useState(false);
  const [isPdfLoading, setIsPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [editingCantidadId, setEditingCantidadId] = useState<string | null>(null);
  const [cantidadValue, setCantidadValue] = useState<string>("");
  const toast = useToast();

  const { data: empresas } = useQuery({
    queryKey: ["empresas"],
    queryFn: () => empresasApi.list().then((r) => r.data.results ?? r.data),
  });

  const { data: inventario, isLoading } = useQuery({
    queryKey: ["inventario", selectedEmpresa],
    queryFn: () =>
      inventarioApi
        .list(selectedEmpresa || undefined)
        .then((r) => r.data.results ?? r.data),
  });

  const [emailError, setEmailError] = useState<string | null>(null);

  const emailMutation = useMutation({
    mutationFn: (data: EmailFormValues) =>
      inventarioApi.exportEmail({ empresa_nit: selectedEmpresa, ...data }),
    onSuccess: () => {
      setEmailSent(true);
      setEmailError(null);
      toast.success("PDF enviado al correo exitosamente.");
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
        "No se pudo enviar el email.";
      setEmailError(msg);
      toast.error(msg);
    },
  });

  const { mutate: updateCantidad, isPending: savingCantidad } = useMutation({
    mutationFn: ({ id, cantidad }: { id: string; cantidad: number }) =>
      inventarioApi.update(id, { cantidad }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventario"] });
      setEditingCantidadId(null);
      toast.success("Cantidad actualizada.");
    },
    onError: () => toast.error("No se pudo actualizar la cantidad."),
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EmailFormValues>({ resolver: zodResolver(emailSchema) });

  const handleDownloadPdf = async () => {
    if (!selectedEmpresa) return;
    setIsPdfLoading(true);
    setPdfError(null);
    try {
      const response = await inventarioApi.exportPdf(selectedEmpresa);
      const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `inventario_${selectedEmpresa}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
        "No se pudo generar el PDF.";
      setPdfError(msg);
    } finally {
      setIsPdfLoading(false);
    }
  };

  return (
    <DashboardTemplate title="Inventario">
      <div className="space-y-6">
        {/* Filters */}
        <div className="bg-white rounded-xl border p-4 flex gap-4 items-end">
          <div className="flex-1">
            <label htmlFor="empresa-filter" className="block text-sm font-medium text-gray-700 mb-1">
              Filtrar por empresa
            </label>
            <select
              id="empresa-filter"
              value={selectedEmpresa}
              onChange={(e) => setSelectedEmpresa(e.target.value)}
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">Todas las empresas</option>
              {empresas?.map((e: { nit: string; nombre: string }) => (
                <option key={e.nit} value={e.nit}>
                  {e.nombre}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Inventory table */}
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {["Código", "Producto", "Empresa", "Características", "Precios", "Cantidad", ""].map((h) => (
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
                        <div className={`h-4 bg-gray-200 rounded animate-pulse`} style={{ width: `${w}%` }} />
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                (inventario as InventarioItem[])?.map((item) => (
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
                            onChange={(e) => setCantidadValue(e.target.value)}
                            className="w-20 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === "Enter") updateCantidad({ id: item.id, cantidad: Number(cantidadValue) });
                              if (e.key === "Escape") setEditingCantidadId(null);
                            }}
                          />
                          <button
                            onClick={() => updateCantidad({ id: item.id, cantidad: Number(cantidadValue) })}
                            disabled={savingCantidad}
                            className="text-green-600 hover:text-green-800"
                            aria-label="Guardar cantidad"
                          >
                            <Check className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setEditingCantidadId(null)}
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
                        onClick={() => { setEditingCantidadId(item.id); setCantidadValue(String(item.cantidad)); }}
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

        {/* Export / Email section */}
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Exportar inventario</h2>
            {selectedEmpresa ? (
              <span className="text-sm text-gray-500">
                Empresa:{" "}
                <span className="font-medium text-gray-900">
                  {empresas?.find((e: { nit: string; nombre: string }) => e.nit === selectedEmpresa)?.nombre ?? selectedEmpresa}
                </span>
              </span>
            ) : (
              <span className="text-sm text-amber-800 bg-amber-50 px-3 py-1 rounded-full border border-amber-200">
                Selecciona una empresa en el filtro para exportar
              </span>
            )}
          </div>

          {emailSent && (
            <div className="mb-4 text-sm text-green-700 bg-green-50 rounded-md px-3 py-2">
              PDF enviado exitosamente al correo indicado.
            </div>
          )}
          {emailError && (
            <div className="mb-4 text-sm text-red-600 bg-red-50 rounded-md px-3 py-2">
              {emailError}
            </div>
          )}
          {pdfError && (
            <div className="mb-4 text-sm text-red-600 bg-red-50 rounded-md px-3 py-2">
              {pdfError}
            </div>
          )}

          <form
            onSubmit={handleSubmit((v) => { setEmailSent(false); setEmailError(null); emailMutation.mutate(v); })}
            className="flex flex-col sm:flex-row gap-4"
          >
            <div className="flex-1">
              <FormField id="recipient_email" label="Correo destinatario" error={errors.recipient_email?.message}>
                <Input
                  {...register("recipient_email")}
                  type="email"
                  placeholder="destinatario@correo.com"
                  error={!!errors.recipient_email}
                  disabled={!selectedEmpresa}
                />
              </FormField>
            </div>
            <div className="flex items-end gap-2">
              <Button
                type="button"
                variant="secondary"
                loading={isPdfLoading}
                disabled={!selectedEmpresa}
                onClick={handleDownloadPdf}
              >
                <Download className="h-4 w-4" /> Descargar PDF
              </Button>
              <Button
                type="submit"
                loading={isSubmitting || emailMutation.isPending}
                disabled={!selectedEmpresa}
              >
                <Mail className="h-4 w-4" /> Enviar por email
              </Button>
            </div>
          </form>
        </div>
      </div>
    </DashboardTemplate>
  );
}
