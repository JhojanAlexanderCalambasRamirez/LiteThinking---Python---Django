import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = Cookies.get("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh/`, { refresh });
          Cookies.set("access_token", data.access, { secure: true, sameSite: "strict" });
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        } catch {
          Cookies.remove("access_token");
          Cookies.remove("refresh_token");
          window.location.href = "/login";
        }
      }
    }

    return Promise.reject(error);
  }
);

// --- Empresas ---
export const empresasApi = {
  list: () => api.get("/empresas/"),
  get: (nit: string) => api.get(`/empresas/${nit}/`),
  create: (data: object) => api.post("/empresas/", data),
  update: (nit: string, data: object) => api.patch(`/empresas/${nit}/`, data),
  delete: (nit: string) => api.delete(`/empresas/${nit}/`),
};

// --- Productos ---
export const productosApi = {
  list: (empresaNit?: string, page?: number) =>
    api.get("/productos/", {
      params: { ...(empresaNit ? { empresa: empresaNit } : {}), ...(page && page > 1 ? { page } : {}) },
    }),
  get: (id: string) => api.get(`/productos/${id}/`),
  create: (data: object) => api.post("/productos/", data),
  update: (id: string, data: object) => api.patch(`/productos/${id}/`, data),
  delete: (id: string) => api.delete(`/productos/${id}/`),
  addPrecio: (productoId: string, data: object) =>
    api.post(`/productos/${productoId}/precios/`, data),
};

// --- Monedas ---
export const monedasApi = {
  list: () => api.get("/monedas/"),
};

// --- Inventario ---
export const inventarioApi = {
  list: (empresaNit?: string) =>
    api.get("/inventario/", { params: empresaNit ? { empresa: empresaNit } : {} }),
  create: (data: object) => api.post("/inventario/", data),
  update: (id: string, data: object) => api.patch(`/inventario/${id}/`, data),
  delete: (id: string) => api.delete(`/inventario/${id}/`),
  exportEmail: (data: object) => api.post("/inventario/export-email/", data),
  exportPdf: (empresaNit: string) =>
    api.post("/inventario/export-pdf/", { empresa_nit: empresaNit }, { responseType: "blob" }),
};

// --- Auth ---
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login/", { email, password }),
  me: () => api.get("/users/me/"),
};

// --- Users ---
export const usersApi = {
  register: (data: { email: string; password: string; nombre: string; apellido?: string }) =>
    api.post("/users/register/", data),
  list: () => api.get("/users/"),
};

// --- AI Agent ---
export const aiAgentApi = {
  query: (query: string, empresa_nit?: string) =>
    axios.post(
      `${process.env.NEXT_PUBLIC_AI_AGENT_URL}/api/v1/agent/query/`,
      { query, empresa_nit }
    ),
  search: (query: string, empresa_nit?: string) =>
    axios.post(
      `${process.env.NEXT_PUBLIC_AI_AGENT_URL}/api/v1/agent/search/`,
      { query, empresa_nit }
    ),
};
