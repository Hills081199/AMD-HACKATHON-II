"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CircleUserRound, LogOut, User, Crown, ChevronDown } from "lucide-react";
import { useAuth } from "../lib/auth-context";

export function UserMenu() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    setIsOpen(false);
    router.push("/");
  };

  if (isLoading) {
    return (
      <div className="h-6 w-6 animate-pulse rounded-full bg-surface-container" />
    );
  }

  if (!isAuthenticated) {
    return (
      <Link
        href="/login"
        className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary transition-colors hover:bg-primary/90"
      >
        <CircleUserRound size={18} />
        Sign in
      </Link>
    );
  }

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg border border-outline-variant bg-surface-container px-3 py-2 text-on-surface transition-colors hover:bg-outline-variant"
      >
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20">
          <User size={14} className="text-primary" />
        </div>
        <span className="max-w-[100px] truncate text-sm">
          {user?.display_name || user?.email?.split("@")[0]}
        </span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-xl border border-outline-variant bg-surface-container shadow-xl">
          <div className="border-b border-outline-variant p-4">
            <p className="font-medium text-on-surface">
              {user?.display_name || "No name set"}
            </p>
            <p className="text-sm text-on-surface-variant">{user?.email}</p>
            <span className="mt-2 inline-block rounded-full bg-primary/20 px-2 py-0.5 text-xs font-medium capitalize text-primary">
              {user?.tier}
            </span>
          </div>

          <div className="p-2">
            <Link
              href="/profile"
              onClick={() => setIsOpen(false)}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-on-surface hover:bg-outline-variant"
            >
              <User size={16} />
              Profile
            </Link>

            {user?.role === "admin" && (
              <Link
                href="/admin"
                onClick={() => setIsOpen(false)}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-tertiary hover:bg-outline-variant"
              >
                <Crown size={16} />
                Admin Dashboard
              </Link>
            )}

            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-error hover:bg-error/10"
            >
              <LogOut size={16} />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
