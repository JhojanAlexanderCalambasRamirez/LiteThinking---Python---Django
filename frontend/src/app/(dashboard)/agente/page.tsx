"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Send, Bot } from "lucide-react";

import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { Spinner } from "@/components/atoms/Spinner";
import { aiAgentApi, empresasApi } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function AgentePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedEmpresa, setSelectedEmpresa] = useState("");

  const { data: empresas } = useQuery({
    queryKey: ["empresas"],
    queryFn: () => empresasApi.list().then((r) => r.data.results ?? r.data),
  });

  const sendQuery = async () => {
    if (!input.trim()) return;
    const userMessage = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await aiAgentApi.query(userMessage, selectedEmpresa || undefined);
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error al conectar con el agente. Intente más tarde." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardTemplate title="Agente IA - Búsqueda Semántica">
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="bg-blue-50 rounded-xl p-4 text-sm text-blue-800">
          <strong>Agente de Inventario</strong> - Haz preguntas en lenguaje natural sobre productos y empresas.
          Usa pgvector para búsqueda semántica y Groq (LLaMA 3.3) para razonamiento.
        </div>

        <div className="flex gap-3">
          <select
            value={selectedEmpresa}
            onChange={(e) => setSelectedEmpresa(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Todas las empresas</option>
            {empresas?.map((e: { nit: string; nombre: string }) => (
              <option key={e.nit} value={e.nit}>{e.nombre}</option>
            ))}
          </select>
        </div>

        <div className="bg-white rounded-xl border shadow-sm min-h-[400px] flex flex-col">
          <div className="flex-1 p-4 space-y-3 overflow-y-auto">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2">
                <Bot className="h-12 w-12 text-gray-300" />
                <p className="text-sm">Pregunta algo sobre el inventario…</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
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
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2">
                  <Spinner size="sm" />
                </div>
              </div>
            )}
          </div>
          <div className="border-t p-3 flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendQuery()}
              placeholder="Ej: ¿Qué laptops tienen más de 16GB RAM?"
              className="flex-1"
            />
            <Button onClick={sendQuery} disabled={loading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </DashboardTemplate>
  );
}
