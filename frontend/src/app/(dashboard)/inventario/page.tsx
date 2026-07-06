"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Download, Mail } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { Spinner } from "@/components/atoms/Spinner";
import { FormField } from "@/components/molecules/FormField";
import { CurrencyDisplay } from "@/components/molecules/CurrencyDisplay";
import { inventarioApi, empresasApi } from "@/lib/api";
import { InventarioItem } from "@/types";

const emailSchema = z.object({
  empresa_nit: z.string().min(1, "Seleccione una empresa"),
  recipient_email: z.string().email("Email inválido"),
});

type EmailFormValues = z.infer<typeof emailSchema>;

export default function InventarioPage() {
  const [selectedEmpresa, setSelectedEmpresa] = useState<string>("");
  const [emailSent, setEmailSent] = useState(false);

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

  const emailMutation = useMutation({
    mutationFn: (data: EmailFormValues) => inventarioApi.exportEmail(data),
    onSuccess: () => setEmailSent(true),
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EmailFormValues>({ resolver: zodResolver(emailSchema) });

  return (
    <DashboardTemplate title="Inventario">
      <div className="space-y-6">
        {/* Filters */}
        <div className="bg-white rounded-xl border p-4 flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filtrar por empresa
            </label>
            <select
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
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {["Código", "Producto", "Empresa", "Características", "Precios", "Cantidad"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {(inventario as InventarioItem[])?.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-sm">{item.producto_detail.codigo}</td>
                    <td className="px-4 py-3 text-sm font-medium">{item.producto_detail.nombre}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{item.empresa_nombre}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                      {item.producto_detail.caracteristicas || "-"}
                    </td>
                    <td className="px-4 py-3">
                      <CurrencyDisplay precios={item.producto_detail.precios} />
                    </td>
                    <td className="px-4 py-3 text-sm font-semibold">{item.cantidad}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!inventario?.length && (
              <div className="text-center py-12 text-gray-500">No hay registros en inventario.</div>
            )}
          </div>
        )}

        {/* Export / Email section */}
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-4">Exportar inventario</h3>
          {emailSent && (
            <div className="mb-4 text-sm text-green-700 bg-green-50 rounded-md px-3 py-2">
              PDF enviado exitosamente al correo indicado.
            </div>
          )}
          <form onSubmit={handleSubmit((v) => emailMutation.mutate(v))} className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <FormField id="exp_empresa" label="Empresa" error={errors.empresa_nit?.message}>
                <select
                  {...register("empresa_nit")}
                  className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">Seleccionar empresa…</option>
                  {empresas?.map((e: { nit: string; nombre: string }) => (
                    <option key={e.nit} value={e.nit}>{e.nombre}</option>
                  ))}
                </select>
              </FormField>
            </div>
            <div className="flex-1">
              <FormField id="recipient_email" label="Correo destinatario" error={errors.recipient_email?.message}>
                <Input
                  {...register("recipient_email")}
                  type="email"
                  placeholder="destinatario@correo.com"
                  error={!!errors.recipient_email}
                />
              </FormField>
            </div>
            <div className="flex items-end">
              <Button type="submit" loading={isSubmitting || emailMutation.isPending}>
                <Mail className="h-4 w-4" /> Enviar PDF
              </Button>
            </div>
          </form>
        </div>
      </div>
    </DashboardTemplate>
  );
}
