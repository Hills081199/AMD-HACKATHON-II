"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, LogIn, Loader2 } from "lucide-react";
import { useAuth } from "../lib/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await login(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-surface px-4">
      <div className="pointer-events-none fixed inset-0 z-0 bg-graph-pattern opacity-20" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-surface via-surface/90 to-surface" />

      <div className="z-10 w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="text-headline-lg font-bold text-on-surface">
            Atlas
          </Link>
          <h1 className="mt-4 text-2xl font-semibold text-on-surface">Welcome back</h1>
          <p className="mt-2 text-on-surface-variant">Sign in to continue your learning journey</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-panel rounded-xl p-8">
          {error && (
            <div className="mb-4 rounded-lg bg-error/10 p-3 text-sm text-error">{error}</div>
          )}

          <div className="mb-4">
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-on-surface">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-outline-variant bg-surface-container px-4 py-3 text-on-surface placeholder-outline focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              placeholder="you@example.com"
              required
            />
          </div>

          <div className="mb-4">
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-on-surface">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-outline-variant bg-surface-container px-4 py-3 pr-12 text-on-surface placeholder-outline focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          <div className="mb-6 flex items-center justify-end">
            <Link
              href="/forgot-password"
              className="text-sm text-primary hover:text-primary/80"
            >
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 font-medium text-on-primary transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <LogIn size={20} />
            )}
            {isLoading ? "Signing in..." : "Sign in"}
          </button>

          <p className="mt-6 text-center text-sm text-on-surface-variant">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-medium text-primary hover:text-primary/80">
              Create one
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
