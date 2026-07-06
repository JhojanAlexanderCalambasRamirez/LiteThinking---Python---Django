"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

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
}

export function CompanyForm({ defaultValues, onSubmit, isEditing, loading }: CompanyFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EmpresaFormValues>({
    resolver: zodResolver(empresaSchema),
    defaultValues,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <FormField id="nit" label="NIT" required error={errors.nit?.message} hint="Formato: 900123456-7">
        <Input
          id="nit"
          placeholder="900123456-7"
          error={!!errors.nit}
          disabled={isEditing}
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
        <Input id="telefono" placeholder="+57 601 234 5678" error={!!errors.telefono} {...register("telefono")} />
      </FormField>

      <div className="pt-2">
        <Button type="submit" loading={isSubmitting || loading} className="w-full">
          {isEditing ? "Actualizar empresa" : "Registrar empresa"}
        </Button>
      </div>
    </form>
  );
}
