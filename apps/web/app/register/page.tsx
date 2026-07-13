"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2, ArrowRight, Sparkles, BookOpen, Brain, Check, X } from "lucide-react";
import { useAuth } from "../lib/auth-context";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Password validation
  const hasMinLength = password.length >= 8;
  const hasUppercase = /[A-Z]/.test(password);
  const hasNumber = /\d/.test(password);
  const isPasswordValid = hasMinLength && hasUppercase && hasNumber;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!isPasswordValid) {
      setError("Password does not meet requirements");
      return;
    }

    setIsLoading(true);

    try {
      await register(email, password, displayName || undefined);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  const PasswordRequirement = ({ met, text }: { met: boolean; text: string }) => (
    <div className={`flex items-center gap-2 text-xs ${met ? "text-tertiary" : "text-on-surface-variant"}`}>
      {met ? <Check size={12} className="shrink-0" /> : <X size={12} className="shrink-0" />}
      {text}
    </div>
  );

  return (
    <div className="flex min-h-screen">
      {/* Left Panel - Cover Image */}
      <div className="relative hidden w-1/2 lg:block">
        {/* Background Image */}
        <Image
          src="/cover.jpg"
          alt="Library bookshelf"
          fill
          className="object-cover"
          priority
        />
        {/* Dark Overlay for better text contrast */}
        <div className="absolute inset-0 bg-black/50" />
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-secondary/60 via-primary/40 to-tertiary/30" />

        {/* Content Overlay */}
        <div className="relative z-10 flex h-full flex-col justify-between p-12">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-white">Atlas</span>
          </div>

          {/* Quote */}
          <div className="max-w-md">
            <blockquote className="text-2xl font-light leading-relaxed text-white/95">
              &ldquo;Start your personalized learning journey today. Upload any document and let AI create your skill tree.&rdquo;
            </blockquote>

            {/* Features */}
            <div className="mt-8 space-y-3">
              {[
                "AI-generated learning paths",
                "Interactive skill trees",
                "Progress tracking & quizzes",
              ].map((feature, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-white/20">
                    <Check size={14} className="text-white" />
                  </div>
                  <span className="text-sm text-white/90">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Features */}
          <div className="flex items-center gap-6 text-sm text-white/70">
            <div className="flex items-center gap-2">
              <BookOpen size={16} />
              <span>PDF, PPTX, DOCX</span>
            </div>
            <div className="flex items-center gap-2">
              <Brain size={16} />
              <span>AI-Powered</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="flex w-full flex-col justify-center bg-surface px-8 py-12 lg:w-1/2 lg:px-16">
        <div className="mx-auto w-full max-w-md">
          {/* Mobile Logo */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <span className="text-xl font-bold text-on-surface">Atlas</span>
          </div>

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-on-surface">Create an account</h1>
            <p className="mt-2 text-on-surface-variant">
              Start your personalized learning journey
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg border border-error/20 bg-error/10 p-4 text-sm text-error">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="displayName" className="mb-2 block text-sm font-medium text-on-surface">
                Display Name <span className="text-outline">(optional)</span>
              </label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg border border-outline-variant bg-surface-container px-4 py-3 text-on-surface placeholder-outline transition-colors focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="Your name"
              />
            </div>

            <div>
              <label htmlFor="email" className="mb-2 block text-sm font-medium text-on-surface">
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-outline-variant bg-surface-container px-4 py-3 text-on-surface placeholder-outline transition-colors focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-2 block text-sm font-medium text-on-surface">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-outline-variant bg-surface-container px-4 py-3 pr-12 text-on-surface placeholder-outline transition-colors focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
                <PasswordRequirement met={hasMinLength} text="8+ characters" />
                <PasswordRequirement met={hasUppercase} text="1 uppercase" />
                <PasswordRequirement met={hasNumber} text="1 number" />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !isPasswordValid}
              className="group mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3.5 font-medium text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary/90 hover:shadow-xl hover:shadow-primary/30 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  Create account
                  <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <p className="mt-8 text-center text-sm text-on-surface-variant">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-primary hover:text-primary/80 transition-colors">
              Sign in
            </Link>
          </p>

          {/* Footer */}
          <p className="mt-8 text-center text-xs text-outline">
            © 2026 Atlas. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
