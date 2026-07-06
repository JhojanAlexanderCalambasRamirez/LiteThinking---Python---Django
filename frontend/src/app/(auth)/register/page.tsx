"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";

import { AuthTemplate } from "@/components/templates/AuthTemplate";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { FormField } from "@/components/molecules/FormField";
import { usersApi } from "@/lib/api";

const registerSchema = z.object({
  email: z.string().email("Email inválido"),
  password: z.string().min(8, "Mínimo 8 caracteres"),
  nombre: z.string().min(2, "Mínimo 2 caracteres"),
  apellido: z.string().optional(),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  const onSubmit = async (data: RegisterFormValues) => {
    try {
      await usersApi.register(data);
      router.push("/login?registered=1");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { email?: string[] } } })?.response?.data?.email?.[0] ??
        "Error al registrar. Intente de nuevo.";
      setError("email", { message: msg });
    }
  };

  return (
    <AuthTemplate title="Crear cuenta" subtitle="Registro como usuario externo">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <FormField id="nombre" label="Nombre" required error={errors.nombre?.message}>
          <Input id="nombre" placeholder="Juan" error={!!errors.nombre} {...register("nombre")} />
        </FormField>

        <FormField id="apellido" label="Apellido" error={errors.apellido?.message}>
          <Input id="apellido" placeholder="Pérez" {...register("apellido")} />
        </FormField>

        <FormField id="email" label="Correo electrónico" required error={errors.email?.message}>
          <Input id="email" type="email" placeholder="juan@correo.com" error={!!errors.email} {...register("email")} />
        </FormField>

        <FormField id="password" label="Contraseña" required error={errors.password?.message}>
          <Input id="password" type="password" placeholder="Mínimo 8 caracteres" error={!!errors.password} {...register("password")} />
        </FormField>

        <div className="pt-2 space-y-3">
          <Button type="submit" loading={isSubmitting} className="w-full">
            Registrarse
          </Button>
          <p className="text-center text-sm text-gray-500">
            ¿Ya tienes cuenta?{" "}
            <Link href="/login" className="text-brand-600 hover:underline font-medium">
              Iniciar sesión
            </Link>
          </p>
        </div>
      </form>
    </AuthTemplate>
  );
}
