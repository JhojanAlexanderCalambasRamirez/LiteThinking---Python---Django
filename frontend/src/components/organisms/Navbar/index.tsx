"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Building2, Package, ClipboardList, Bot } from "lucide-react";
import { clsx } from "clsx";

import { Button } from "@/components/atoms/Button";
import { Badge } from "@/components/atoms/Badge";
import { clearTokens, getCurrentUser } from "@/lib/auth";

const navItems = [
  { href: "/empresas", label: "Empresas", icon: Building2 },
  { href: "/productos", label: "Productos", icon: Package, adminOnly: true },
  { href: "/inventario", label: "Inventario", icon: ClipboardList, adminOnly: true },
  { href: "/agente", label: "Agente IA", icon: Bot, adminOnly: true },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<ReturnType<typeof getCurrentUser>>(null);

  useEffect(() => {
    setUser(getCurrentUser());
  }, []);

  const handleLogout = () => {
    clearTokens();
    router.push("/login");
  };

  return (
    <nav className="bg-brand-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <span className="text-lg font-bold tracking-tight">LiteThinking</span>
            <div className="flex gap-1">
              {navItems.map(({ href, label, icon: Icon, adminOnly }) => {
                if (adminOnly && user?.rol !== "admin") return null;
                return (
                  <Link
                    key={href}
                    href={href}
                    className={clsx(
                      "flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                      pathname.startsWith(href)
                        ? "bg-brand-600 text-white"
                        : "text-gray-300 hover:bg-brand-700 hover:text-white"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={user?.rol === "admin" ? "info" : "neutral"}>
              {user?.rol === "admin" ? "Administrador" : "Externo"}
            </Badge>
            <span className="text-sm text-gray-300">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={handleLogout} className="text-gray-300 hover:text-white">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}
