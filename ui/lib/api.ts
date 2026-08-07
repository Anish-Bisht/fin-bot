import { clearCurrentUser } from "@/lib/threads";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export function getToken() {
  if (typeof window !== "undefined") {
    return localStorage.getItem("token");
  }
  return null;
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("token", token);
  }
}

export function logout() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("token");
    clearCurrentUser();
    window.location.href = "/login";
  }
}

function getHeaders() {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function login(username: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const res = await fetch(`${API_BASE}/chat/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString(),
  });

  if (!res.ok) throw new Error("Login failed");
  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function getUserMe() {
  const res = await fetch(`${API_BASE}/chat/me`, { headers: getHeaders() });
  if (!res.ok) {
    if (res.status === 401) logout();
    throw new Error("Failed to authenticate");
  }
  return res.json();
}

export async function sendMessage(query: string, threadId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/chat/brief`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ query, thread_id: threadId }),
  });

  if (!res.ok) {
    if (res.status === 401) logout();
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  const data = await res.json();
  return data;
}

// Admin functionality
export async function getUsers() {
  const res = await fetch(`${API_BASE}/admin/users`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch users");
  return res.json();
}

export async function createUser(data: any) {
  const res = await fetch(`${API_BASE}/admin/users`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create user");
  return res.json();
}

export async function updateUser(username: string, data: any) {
  const res = await fetch(`${API_BASE}/admin/users/${username}`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update user");
  return res.json();
}

export async function deleteUser(username: string) {
  const res = await fetch(`${API_BASE}/admin/users/${username}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to delete user");
  return res.json();
}

export async function getDocuments() {
  const res = await fetch(`${API_BASE}/admin/documents`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function addDocument(formData: FormData) {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  const res = await fetch(`${API_BASE}/admin/documents`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to add document");
  return res.json();
}

export async function deleteDocument(docId: string) {
  const res = await fetch(`${API_BASE}/admin/documents/${docId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to delete document");
  return res.json();
}
