import { ProductoPrecio } from "@/types";

interface CurrencyDisplayProps {
  precios: ProductoPrecio[];
}

export function CurrencyDisplay({ precios }: CurrencyDisplayProps) {
  if (!precios.length) return <span className="text-gray-400 text-sm">Sin precios</span>;

  return (
    <div className="flex flex-wrap gap-1">
      {precios.map((p) => (
        <span
          key={p.moneda_codigo}
          className="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700"
        >
          <span className="text-gray-500">{p.moneda_simbolo}</span>
          {Number(p.precio).toLocaleString("es-CO", { minimumFractionDigits: 2 })}
          <span className="text-gray-600">{p.moneda_codigo}</span>
        </span>
      ))}
    </div>
  );
}
