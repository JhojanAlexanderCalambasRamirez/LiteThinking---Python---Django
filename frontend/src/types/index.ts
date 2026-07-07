export type UserRole = "admin" | "externo";

export interface User {
  id: string;
  email: string;
  nombre: string | null;
  apellido: string | null;
  rol: UserRole;
  activo: boolean;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface Empresa {
  nit: string;
  nombre: string;
  direccion: string;
  telefono: string;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmpresaForm {
  nit: string;
  nombre: string;
  direccion: string;
  telefono: string;
}

export interface Moneda {
  codigo: string;
  nombre: string;
  simbolo: string;
}

export interface ProductoPrecio {
  id: string;
  moneda_codigo: string;
  moneda_nombre: string;
  moneda_simbolo: string;
  precio: string;
}

export interface Producto {
  id: string;
  codigo: string;
  nombre: string;
  caracteristicas: string | null;
  empresa_nit: string;
  empresa_nombre?: string;
  activo: boolean;
  precios: ProductoPrecio[];
  created_at: string;
  updated_at: string;
}

export interface ProductoForm {
  codigo: string;
  nombre: string;
  caracteristicas?: string;
  empresa_nit: string;
  precios: { moneda_codigo: string; precio: number }[];
}

export interface InventarioItem {
  id: string;
  producto: string;
  producto_detail: Producto;
  empresa_nit: string;
  empresa_nombre: string;
  cantidad: number;
  observaciones: string | null;
  created_by_email: string;
  created_at: string;
  updated_at: string;
}

export interface InventarioForm {
  producto: string;
  cantidad: number;
  observaciones?: string;
}

export interface ExportEmailForm {
  empresa_nit: string;
  recipient_email: string;
}

export interface AgentQueryResponse {
  query: string;
  response: string;
}

export interface BlockchainLog {
  id: string;
  entity_type: string;
  entity_id: string;
  accion: "CREATE" | "UPDATE" | "DELETE";
  data_hash: string;
  tx_hash: string | null;
  block_number: number | null;
  network: string | null;
  created_at: string;
  on_chain: boolean;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
