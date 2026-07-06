"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";

import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { FormField } from "@/components/molecules/FormField";
import { authApi } from "@/lib/api";
import { setTokens } from "@/lib/auth";

const loginSchema = z.object({
  email: z.string().email("Correo electrónico inválido"),
  password: z.string().min(1, "La contraseña es requerida"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    setServerError(null);
    try {
      const response = await authApi.login(data.email, data.password);
      setTokens(response.data.access, response.data.refresh);
      router.push("/empresas");
    } catch {
      setServerError("Correo o contraseña incorrectos. Intente de nuevo.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
      <FormField id="email" label="Correo electrónico" required error={errors.email?.message}>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="usuario@empresa.com"
          error={!!errors.email}
          {...register("email")}
        />
      </FormField>

      <FormField id="password" label="Contraseña" required error={errors.password?.message}>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          error={!!errors.password}
          {...register("password")}
        />
      </FormField>

      {serverError && (
        <p className="text-sm text-red-600 bg-red-50 rounded-md px-3 py-2" role="alert">
          {serverError}
        </p>
      )}

      <Button type="submit" className="w-full" loading={isSubmitting}>
        Iniciar Sesión
      </Button>
    </form>
  );
}
