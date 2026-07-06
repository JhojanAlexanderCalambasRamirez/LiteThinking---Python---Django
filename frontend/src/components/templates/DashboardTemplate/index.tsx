import { ReactNode } from "react";
import { Navbar } from "@/components/organisms/Navbar";

interface DashboardTemplateProps {
  title: string;
  children: ReactNode;
  actions?: ReactNode;
}

export function DashboardTemplate({ title, children, actions }: DashboardTemplateProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header>
        <Navbar />
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6 min-h-[40px]">
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          <div className="flex gap-3">{actions}</div>
        </div>
        {children}
      </main>
    </div>
  );
}
