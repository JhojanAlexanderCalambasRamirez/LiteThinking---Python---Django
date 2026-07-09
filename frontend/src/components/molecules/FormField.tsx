import { ReactNode } from "react";
import { Label } from "@/components/atoms/Label";

interface FormFieldProps {
  id: string;
  label: string;
  required?: boolean;
  error?: string;
  hint?: string;
  children: ReactNode;
}

export function FormField({ id, label, required, error, hint, children }: FormFieldProps) {
  return (
    <div className="space-y-1">
      <Label htmlFor={id} required={required}>
        {label}
      </Label>
      {children}
      {hint && !error && <p className="text-xs text-gray-500">{hint}</p>}
      {error && (
        <p className="text-xs text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
