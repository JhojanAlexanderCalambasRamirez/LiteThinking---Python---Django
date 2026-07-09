import { InputHTMLAttributes, forwardRef } from "react";
import { clsx } from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ error, className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={clsx(
          "block w-full rounded-md border px-3 py-2 text-sm shadow-sm",
          "placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-0",
          "disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500",
          error
            ? "border-red-300 focus:border-red-400 focus:ring-red-300"
            : "border-gray-300 focus:border-brand-500 focus:ring-brand-500",
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";
