"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail, Loader2, ArrowLeft, CheckCircle } from "lucide-react";
import { authApi } from "../lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await authApi.forgotPassword(email);
      setIsSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send reset email");
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-surface px-4">
        <div className="pointer-events-none fixed inset-0 z-0 bg-graph-pattern opacity-20" />
        <div className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-surface via-surface/90 to-surface" />

        <div className="z-10 w-full max-w-md">
          <div className="glass-panel rounded-xl p-8 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-tertiary/20">
              <CheckCircle size={32} className="text-tertiary" />
            </div>
            <h1 className="mb-2 text-2xl font-semibold text-on-surface">Check your email</h1>
            <p className="mb-6 text-on-surface-variant">
              If an account exists for <span className="font-medium text-on-surface">{email}</span>,
              you&apos;ll receive a password reset link shortly.
            </p>
            <Link
              href="/login"
              className="flex items-center justify-center gap-2 text-primary hover:text-primary/80"
            >
              <ArrowLeft size={16} />
              Back to login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-surface px-4">
      <div className="pointer-events-none fixed inset-0 z-0 bg-graph-pattern opacity-20" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-surface via-surface/90 to-surface" />

      <div className="z-10 w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="text-headline-lg font-bold text-on-surface">
            Atlas
          </Link>
          <h1 className="mt-4 text-2xl font-semibold text-on-surface">Reset your password</h1>
          <p className="mt-2 text-on-surface-variant">
            Enter your email and we&apos;ll send you a reset link
          </p>
        </div>

        <form onSubmit={handleSubmit} className="glass-panel rounded-xl p-8">
          {error && (
            <div className="mb-4 rounded-lg bg-error/10 p-3 text-sm text-error">{error}</div>
          )}

          <div className="mb-6">
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

          <button
            type="submit"
            disabled={isLoading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 font-medium text-on-primary transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <Mail size={20} />
            )}
            {isLoading ? "Sending..." : "Send reset link"}
          </button>

          <p className="mt-6 text-center text-sm text-on-surface-variant">
            Remember your password?{" "}
            <Link href="/login" className="font-medium text-primary hover:text-primary/80">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
