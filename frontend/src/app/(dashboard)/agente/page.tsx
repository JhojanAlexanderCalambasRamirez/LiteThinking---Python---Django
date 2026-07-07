"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Bot, ShoppingCart, Plus, Minus, X } from "lucide-react";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { Spinner } from "@/components/atoms/Spinner";
import { aiAgentApi, empresasApi, pedidoApi } from "@/lib/api";
import { useToast } from "@/lib/toast";

interface ProductoSugerido {
  id: string;
  inventario_id: string | null;
  codigo: string;
  nombre: string;
  caracteristicas: string | null;
  empresa_nit: string;
  empresa_nombre: string;
  stock: number;
  similarity: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  productos_sugeridos?: ProductoSugerido[];
}

interface CartItem {
  inventario_id: string;
  producto_codigo: string;
  producto_nombre: string;
  empresa_nombre: string;
  cantidad: number;
  stock: number;
}

export default function AgentePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedEmpresa, setSelectedEmpresa] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: empresas } = useQuery({
    queryKey: ["empresas"],
    queryFn: () => empresasApi.list().then((r) => r.data.results ?? r.data),
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addToCart = (producto: ProductoSugerido) => {
    if (!producto.inventario_id) {
      toast.error("Este producto no tiene inventario registrado.");
      return;
    }
    setCart((prev) => {
      const existing = prev.find((i) => i.inventario_id === producto.inventario_id);
      if (existing) {
        const next = Math.min(existing.cantidad + 1, producto.stock);
        if (next === existing.cantidad) {
          toast.error(`Stock máximo alcanzado para ${producto.nombre}.`);
          return prev;
        }
        return prev.map((i) =>
          i.inventario_id === producto.inventario_id ? { ...i, cantidad: next } : i
        );
      }
      return [
        ...prev,
        {
          inventario_id: producto.inventario_id!,
          producto_codigo: producto.codigo,
          producto_nombre: producto.nombre,
          empresa_nombre: producto.empresa_nombre,
          cantidad: 1,
          stock: producto.stock,
        },
      ];
    });
    toast.success(`${producto.nombre} agregado al carrito.`);
  };

  const updateCartQty = (inventario_id: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((i) =>
          i.inventario_id === inventario_id
            ? { ...i, cantidad: Math.max(0, Math.min(i.cantidad + delta, i.stock)) }
            : i
        )
        .filter((i) => i.cantidad > 0)
    );
  };

  const removeFromCart = (inventario_id: string) => {
    setCart((prev) => prev.filter((i) => i.inventario_id !== inventario_id));
  };

  const pedidoMutation = useMutation({
    mutationFn: () =>
      pedidoApi.confirmar(
        cart.map((i) => ({ inventario_id: i.inventario_id, cantidad: i.cantidad }))
      ),
    onSuccess: () => {
      toast.success("Pedido confirmado. Stock actualizado.");
      setCart([]);
      queryClient.invalidateQueries({ queryKey: ["inventario"] });
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
        "Error al confirmar el pedido.";
      toast.error(msg);
    },
  });

  const sendQuery = async () => {
    if (!input.trim()) return;
    const userMessage = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setLoading(true);

    try {
      const empresaNombre = empresas?.find(
        (e: { nit: string; nombre: string }) => e.nit === selectedEmpresa
      )?.nombre;
      const { data } = await aiAgentApi.query(
        userMessage,
        selectedEmpresa || undefined,
        empresaNombre
      );
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          productos_sugeridos:
            (data.productos_sugeridos as ProductoSugerido[])?.filter(
              (p) => p.inventario_id && p.stock > 0
            ) ?? [],
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error al conectar con el agente. Intente más tarde." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const cartTotal = cart.reduce((sum, i) => sum + i.cantidad, 0);

  return (
    <DashboardTemplate title="Agente IA - Búsqueda Semántica">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6 items-start">
        {/* Chat */}
        <div className="space-y-4">
          <div className="bg-blue-50 rounded-xl p-4 text-sm text-blue-800">
            <strong>Agente de Inventario</strong> — Pregunta en lenguaje natural sobre productos.
            Los resultados aparecen como chips clicables para agregar al carrito.
          </div>

          <div className="flex gap-3">
            <select
              id="agente-empresa-filter"
              value={selectedEmpresa}
              onChange={(e) => setSelectedEmpresa(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-label="Filtrar por empresa"
            >
              <option value="">Todas las empresas</option>
              {empresas?.map((e: { nit: string; nombre: string }) => (
                <option key={e.nit} value={e.nit}>{e.nombre}</option>
              ))}
            </select>
          </div>

          <div className="bg-white rounded-xl border shadow-sm flex flex-col">
            <div className="flex-1 p-4 space-y-4 overflow-y-auto max-h-[520px] min-h-[300px]">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2">
                  <Bot className="h-12 w-12 text-gray-300" />
                  <p className="text-sm">Pregunta algo sobre el inventario…</p>
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className="space-y-2">
                  <div className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2 text-sm whitespace-pre-wrap ${
                        msg.role === "user"
                          ? "bg-brand-600 text-white"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                  {msg.productos_sugeridos && msg.productos_sugeridos.length > 0 && (
                    <div className="flex flex-wrap gap-2 pl-2">
                      {msg.productos_sugeridos.map((p) => (
                        <button
                          key={p.id}
                          onClick={() => addToCart(p)}
                          title={p.caracteristicas ?? ""}
                          className="flex items-center gap-1.5 text-xs bg-white border border-brand-200 text-brand-700 hover:bg-brand-50 rounded-full px-3 py-1.5 transition-colors"
                        >
                          <Plus className="h-3 w-3" />
                          <span className="font-medium">{p.codigo}</span>
                          <span>· {p.nombre}</span>
                          <span className="text-gray-400">({p.stock} disp.)</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg px-4 py-2">
                    <Spinner size="sm" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            <div className="border-t p-3 flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendQuery()}
                placeholder="Ej: ¿Qué laptops tienen más de 16GB RAM?"
                className="flex-1"
              />
              <Button
                onClick={sendQuery}
                disabled={loading || !input.trim()}
                aria-label="Enviar mensaje"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Cart */}
        <div className="bg-white rounded-xl border shadow-sm sticky top-6">
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <div className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5 text-gray-600" />
              <span className="font-semibold text-gray-900">Carrito</span>
              {cartTotal > 0 && (
                <span className="bg-brand-600 text-white text-xs rounded-full px-2 py-0.5 font-medium">
                  {cartTotal}
                </span>
              )}
            </div>
            {cart.length > 0 && (
              <button
                onClick={() => setCart([])}
                className="text-xs text-gray-400 hover:text-red-500 transition-colors"
                aria-label="Vaciar carrito"
              >
                Vaciar
              </button>
            )}
          </div>

          {cart.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400 gap-2">
              <ShoppingCart className="h-10 w-10 text-gray-200" />
              <p className="text-sm text-center px-4">
                Haz clic en los chips de productos para agregarlos
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {cart.map((item) => (
                <div key={item.inventario_id} className="px-4 py-3 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {item.producto_nombre}
                      </p>
                      <p className="text-xs text-gray-500">
                        {item.producto_codigo} · {item.empresa_nombre}
                      </p>
                    </div>
                    <button
                      onClick={() => removeFromCart(item.inventario_id)}
                      className="text-gray-300 hover:text-red-500 transition-colors mt-0.5 flex-shrink-0"
                      aria-label={`Quitar ${item.producto_nombre} del carrito`}
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => updateCartQty(item.inventario_id, -1)}
                      className="rounded border border-gray-200 p-1 hover:bg-gray-50 transition-colors"
                      aria-label="Reducir cantidad"
                    >
                      <Minus className="h-3 w-3" />
                    </button>
                    <span className="text-sm font-semibold w-6 text-center">{item.cantidad}</span>
                    <button
                      onClick={() => updateCartQty(item.inventario_id, 1)}
                      disabled={item.cantidad >= item.stock}
                      className="rounded border border-gray-200 p-1 hover:bg-gray-50 transition-colors disabled:opacity-40"
                      aria-label="Aumentar cantidad"
                    >
                      <Plus className="h-3 w-3" />
                    </button>
                    <span className="text-xs text-gray-400 ml-auto">máx {item.stock}</span>
                  </div>
                </div>
              ))}
              <div className="px-4 py-3">
                <Button
                  className="w-full"
                  loading={pedidoMutation.isPending}
                  onClick={() => pedidoMutation.mutate()}
                >
                  Confirmar pedido ({cartTotal} uds.)
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardTemplate>
  );
}
