import Cookies from "js-cookie";
import { jwtDecode } from "jwt-decode";

interface JWTPayload {
  user_id: string;
  email: string;
  rol: "admin" | "externo";
  nombre: string;
  exp: number;
}

export function getAccessToken(): string | null {
  return Cookies.get("access_token") ?? null;
}

export function setTokens(access: string, refresh: string): void {
  Cookies.set("access_token", access, { secure: true, sameSite: "strict", expires: 1 });
  Cookies.set("refresh_token", refresh, { secure: true, sameSite: "strict", expires: 7 });
}

export function clearTokens(): void {
  Cookies.remove("access_token");
  Cookies.remove("refresh_token");
}

export function getCurrentUser(): JWTPayload | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    if (decoded.exp * 1000 < Date.now()) {
      clearTokens();
      return null;
    }
    return decoded;
  } catch {
    return null;
  }
}

export function isAdmin(): boolean {
  return getCurrentUser()?.rol === "admin";
}

export function isAuthenticated(): boolean {
  return getCurrentUser() !== null;
}
