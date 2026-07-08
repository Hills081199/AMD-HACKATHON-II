export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  role: "user" | "admin";
  tier: "free" | "trial" | "premium";
  created_at: string;
  last_login_at: string | null;
  trial_expires_at: string | null;
}

export interface UsageStats {
  documents_used: number;
  documents_limit: number;
  skill_trees_created: number;
  skill_trees_limit: number;
  quizzes_completed: number;
  chat_messages_today: number;
  chat_messages_limit: number;
  tier: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApiError {
  detail: string;
}
