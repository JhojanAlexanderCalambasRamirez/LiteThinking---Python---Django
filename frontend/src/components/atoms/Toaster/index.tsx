"use client";

import { X, CheckCircle2, XCircle, Info } from "lucide-react";
import { useToast } from "@/lib/toast";

const STYLES = {
  success: {
    wrapper: "bg-green-50 border-green-200 text-green-800",
    icon: <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />,
  },
  error: {
    wrapper: "bg-red-50 border-red-200 text-red-800",
    icon: <XCircle className="h-5 w-5 text-red-500 shrink-0" />,
  },
  info: {
    wrapper: "bg-blue-50 border-blue-200 text-blue-800",
    icon: <Info className="h-5 w-5 text-blue-500 shrink-0" />,
  },
};

export function Toaster() {
  const { toasts, dismiss } = useToast();

  if (!toasts.length) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full">
      {toasts.map((toast) => {
        const { wrapper, icon } = STYLES[toast.type];
        return (
          <div
            key={toast.id}
            className={`flex items-start gap-3 rounded-lg border px-4 py-3 shadow-md text-sm animate-in slide-in-from-right-5 fade-in duration-200 ${wrapper}`}
          >
            {icon}
            <span className="flex-1 leading-snug">{toast.message}</span>
            <button
              onClick={() => dismiss(toast.id)}
              className="shrink-0 opacity-50 hover:opacity-100 transition-opacity"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
