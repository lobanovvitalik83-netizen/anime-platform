import type { Permission, Role, TokenPair, User } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return response.json();
}

export async function login(emailOrUsername: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email_or_username: emailOrUsername,
      password,
    }),
  });
}

export async function fetchMe(): Promise<User> {
  return apiFetch<User>("/api/v1/auth/me");
}

export async function fetchUsers(): Promise<User[]> {
  return apiFetch<User[]>("/api/v1/users");
}

export async function fetchRoles(): Promise<Role[]> {
  return apiFetch<Role[]>("/api/v1/roles");
}

export async function fetchPermissions(): Promise<Permission[]> {
  return apiFetch<Permission[]>("/api/v1/permissions");
}
