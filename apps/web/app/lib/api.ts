const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }));
    throw new Error(error.detail || "An error occurred");
  }

  return response.json();
}

export const authApi = {
  register: (email: string, password: string, displayName?: string) =>
    apiRequest<{ access_token: string; user: import("./types").User }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name: displayName }),
    }),

  login: (email: string, password: string) =>
    apiRequest<{ access_token: string; user: import("./types").User }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: () =>
    apiRequest<{ message: string }>("/api/auth/logout", {
      method: "POST",
    }),

  forgotPassword: (email: string) =>
    apiRequest<{ message: string }>("/api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
};

export const userApi = {
  getProfile: () => apiRequest<import("./types").User>("/api/user/profile"),

  updateProfile: (data: { display_name?: string; avatar_url?: string }) =>
    apiRequest<import("./types").User>("/api/user/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  changePassword: (currentPassword: string, newPassword: string) =>
    apiRequest<{ message: string }>("/api/user/password", {
      method: "PUT",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    }),

  getUsage: () => apiRequest<import("./types").UsageStats>("/api/user/usage"),
};

export const adminApi = {
  listUsers: (page = 1, perPage = 20, search?: string) => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    if (search) params.set("search", search);
    return apiRequest<{
      users: import("./types").User[];
      total: number;
      page: number;
      per_page: number;
    }>(`/api/admin/users?${params}`);
  },

  updateUser: (userId: string, data: { role?: string; tier?: string }) =>
    apiRequest<import("./types").User>(`/api/admin/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteUser: (userId: string) =>
    apiRequest<void>(`/api/admin/users/${userId}`, {
      method: "DELETE",
    }),

  resetUserUsage: (userId: string) =>
    apiRequest<import("./types").User>(`/api/admin/users/${userId}/reset-usage`, {
      method: "POST",
    }),

  getStats: () =>
    apiRequest<{
      total_users: number;
      total_documents: number;
      total_skill_trees: number;
      total_quizzes: number;
      users_by_tier: Record<string, number>;
    }>("/api/admin/stats"),
};
