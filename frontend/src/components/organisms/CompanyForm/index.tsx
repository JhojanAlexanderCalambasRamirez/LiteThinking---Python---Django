"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

function formatTelefono(raw: string): string {
  const digits = raw.replace(/\D/g, "");
  // Colombian mobile/landline: +57 XXX XXX XXXX (10 digits after country code)
  if (digits.startsWith("57") && digits.length === 12) {
    return `+57 ${digits.slice(2, 5)} ${digits.slice(5, 8)} ${digits.slice(8)}`;
  }
  if (!digits.startsWith("57") && digits.length === 10) {
    return `+57 ${digits.slice(0, 3)} ${digits.slice(3, 6)} ${digits.slice(6)}`;
  }
  // Keep original if pattern doesn't match
  return raw.trim();
}

import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { FormField } from "@/components/molecules/FormField";
import { Empresa } from "@/types";

const nitPattern = /^\d{6,10}(-\d)?$/;

const empresaSchema = z.object({
  nit: z.string().regex(nitPattern, "NIT inválido. Ej: 900123456-7"),
  nombre: z.string().min(2, "Mínimo 2 caracteres"),
  direccion: z.string().min(5, "Dirección muy corta"),
  telefono: z.string().min(7, "Teléfono inválido"),
});

export type EmpresaFormValues = z.infer<typeof empresaSchema>;

interface CompanyFormProps {
  defaultValues?: Partial<Empresa>;
  onSubmit: (data: EmpresaFormValues) => Promise<void>;
  isEditing?: boolean;
  loading?: boolean;
  apiError?: string | null;
}

export function CompanyForm({ defaultValues, onSubmit, isEditing, loading, apiError }: CompanyFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<EmpresaFormValues>({
    resolver: zodResolver(empresaSchema),
    defaultValues,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      {apiError && (
        <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 border border-red-200">
          {apiError}
        </div>
      )}
      <FormField
        id="nit"
        label="NIT"
        required
        error={errors.nit?.message}
        hint={isEditing ? "Cambiar NIT actualiza también todos los productos asociados." : "Formato: 900123456-7"}
      >
        <Input
          id="nit"
          placeholder="900123456-7"
          error={!!errors.nit}
          {...register("nit")}
        />
      </FormField>

      <FormField id="nombre" label="Nombre de la empresa" required error={errors.nombre?.message}>
        <Input id="nombre" placeholder="LiteThinking S.A.S." error={!!errors.nombre} {...register("nombre")} />
      </FormField>

      <FormField id="direccion" label="Dirección" required error={errors.direccion?.message}>
        <Input id="direccion" placeholder="Cra 7 # 32-16, Bogotá" error={!!errors.direccion} {...register("direccion")} />
      </FormField>

      <FormField id="telefono" label="Teléfono" required error={errors.telefono?.message}>
        <Input
          id="telefono"
          placeholder="+57 601 234 5678"
          error={!!errors.telefono}
          {...register("telefono", {
            onBlur: (e) => setValue("telefono", formatTelefono(e.target.value), { shouldValidate: true }),
          })}
        />
      </FormField>

      <div className="pt-2">
        <Button type="submit" loading={isSubmitting || loading} className="w-full">
          {isEditing ? "Actualizar empresa" : "Registrar empresa"}
        </Button>
      </div>
    </form>
  );
}
