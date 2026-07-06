import { ReactNode } from "react";

interface AuthTemplateProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function AuthTemplate({ title, subtitle, children }: AuthTemplateProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 to-brand-700 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">LiteThinking</h1>
          {subtitle && <p className="mt-2 text-brand-200">{subtitle}</p>}
        </div>
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">{title}</h2>
          {children}
        </div>
      </div>
    </div>
  );
}
