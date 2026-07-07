"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Download, Mail } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { FormField } from "@/components/molecules/FormField";
import { InventoryTable } from "@/components/organisms/InventoryTable";
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
        <InventoryTable
          inventario={inventario as InventarioItem[]}
          isLoading={isLoading}
          editingCantidadId={editingCantidadId}
          cantidadValue={cantidadValue}
          savingCantidad={savingCantidad}
          onEditStart={(id, cantidad) => { setEditingCantidadId(id); setCantidadValue(String(cantidad)); }}
          onEditSave={(id, cantidad) => updateCantidad({ id, cantidad })}
          onEditCancel={() => setEditingCantidadId(null)}
          onCantidadChange={setCantidadValue}
        />

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
