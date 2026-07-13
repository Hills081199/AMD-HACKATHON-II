"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Users,
  FileText,
  TreeDeciduous,
  HelpCircle,
  Search,
  ArrowLeft,
  Loader2,
  Crown,
  Trash2,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../lib/auth-context";
import { adminApi } from "../lib/api";
import { User } from "../lib/types";

interface SystemStats {
  total_users: number;
  total_documents: number;
  total_skill_trees: number;
  total_quizzes: number;
  users_by_tier: Record<string, number>;
}

export default function AdminPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [totalUsers, setTotalUsers] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const perPage = 10;
  const totalPages = Math.ceil(totalUsers / perPage);

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.push("/");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (user?.role === "admin") {
      adminApi.getStats().then(setStats).catch(console.error);
    }
  }, [user]);

  useEffect(() => {
    if (user?.role === "admin") {
      loadUsers();
    }
  }, [user, page, search]);

  const loadUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const response = await adminApi.listUsers(page, perPage, search || undefined);
      setUsers(response.users);
      setTotalUsers(response.total);
    } catch (error) {
      console.error("Failed to load users:", error);
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const handleUpdateTier = async (userId: string, tier: string) => {
    setActionLoading(userId);
    try {
      await adminApi.updateUser(userId, { tier });
      await loadUsers();
      const newStats = await adminApi.getStats();
      setStats(newStats);
    } catch (error) {
      console.error("Failed to update user:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResetUsage = async (userId: string) => {
    setActionLoading(userId);
    try {
      await adminApi.resetUserUsage(userId);
      await loadUsers();
    } catch (error) {
      console.error("Failed to reset usage:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm("Are you sure you want to delete this user?")) return;
    setActionLoading(userId);
    try {
      await adminApi.deleteUser(userId);
      await loadUsers();
      const newStats = await adminApi.getStats();
      setStats(newStats);
    } catch (error) {
      console.error("Failed to delete user:", error);
    } finally {
      setActionLoading(null);
    }
  };

  if (authLoading || !user || user.role !== "admin") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-surface">
      <div className="pointer-events-none fixed inset-0 z-0 bg-graph-pattern opacity-20" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-surface via-surface/90 to-surface" />

      <header className="fixed top-0 z-50 flex h-16 w-full items-center justify-between border-b border-white/10 bg-surface/70 px-margin-mobile shadow-sm backdrop-blur-xl md:px-margin-desktop">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-headline-lg font-bold text-on-surface">
            Atlas
          </Link>
          <span className="rounded bg-tertiary/20 px-2 py-1 text-xs font-medium text-tertiary">
            Admin
          </span>
        </div>
        <Link
          href="/profile"
          className="flex items-center gap-2 text-on-surface-variant hover:text-on-surface"
        >
          <ArrowLeft size={20} />
          Profile
        </Link>
      </header>

      <main className="relative z-10 mx-auto max-w-6xl px-margin-mobile pb-16 pt-24 md:px-margin-desktop">
        <h1 className="mb-8 text-3xl font-bold text-on-surface">Admin Dashboard</h1>

        {/* Stats Grid */}
        {stats && (
          <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="glass-panel rounded-xl p-6">
              <div className="mb-2 flex items-center gap-2 text-on-surface-variant">
                <Users size={20} />
                <span className="text-sm">Total Users</span>
              </div>
              <p className="text-3xl font-bold text-on-surface">{stats.total_users}</p>
            </div>
            <div className="glass-panel rounded-xl p-6">
              <div className="mb-2 flex items-center gap-2 text-on-surface-variant">
                <FileText size={20} />
                <span className="text-sm">Documents Processed</span>
              </div>
              <p className="text-3xl font-bold text-on-surface">{stats.total_documents}</p>
            </div>
            <div className="glass-panel rounded-xl p-6">
              <div className="mb-2 flex items-center gap-2 text-on-surface-variant">
                <TreeDeciduous size={20} />
                <span className="text-sm">Skill Trees</span>
              </div>
              <p className="text-3xl font-bold text-on-surface">{stats.total_skill_trees}</p>
            </div>
            <div className="glass-panel rounded-xl p-6">
              <div className="mb-2 flex items-center gap-2 text-on-surface-variant">
                <HelpCircle size={20} />
                <span className="text-sm">Quizzes Completed</span>
              </div>
              <p className="text-3xl font-bold text-on-surface">{stats.total_quizzes}</p>
            </div>
          </div>
        )}

        {/* Users by Tier */}
        {stats && (
          <div className="mb-8 glass-panel rounded-xl p-6">
            <h2 className="mb-4 text-lg font-semibold text-on-surface">Users by Tier</h2>
            <div className="flex gap-6">
              {Object.entries(stats.users_by_tier).map(([tier, count]) => (
                <div key={tier} className="text-center">
                  <p className="text-2xl font-bold text-on-surface">{count}</p>
                  <p className="text-sm capitalize text-on-surface-variant">{tier}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* User Management */}
        <div className="glass-panel rounded-xl p-6">
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-lg font-semibold text-on-surface">User Management</h2>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search users..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-lg border border-outline-variant bg-surface-container py-2 pl-10 pr-4 text-on-surface placeholder-outline focus:border-primary focus:outline-none sm:w-64"
              />
            </div>
          </div>

          {isLoadingUsers ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-outline-variant text-left">
                      <th className="pb-3 text-sm font-medium text-on-surface-variant">User</th>
                      <th className="pb-3 text-sm font-medium text-on-surface-variant">Role</th>
                      <th className="pb-3 text-sm font-medium text-on-surface-variant">Tier</th>
                      <th className="pb-3 text-sm font-medium text-on-surface-variant">Usage</th>
                      <th className="pb-3 text-sm font-medium text-on-surface-variant">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id} className="border-b border-outline-variant/50">
                        <td className="py-4">
                          <div>
                            <p className="font-medium text-on-surface">
                              {u.display_name || "No name"}
                            </p>
                            <p className="text-sm text-on-surface-variant">{u.email}</p>
                          </div>
                        </td>
                        <td className="py-4">
                          {u.role === "admin" ? (
                            <span className="flex items-center gap-1 text-tertiary">
                              <Crown size={14} />
                              Admin
                            </span>
                          ) : (
                            <span className="text-on-surface-variant">User</span>
                          )}
                        </td>
                        <td className="py-4">
                          <select
                            value={u.tier}
                            onChange={(e) => handleUpdateTier(u.id, e.target.value)}
                            disabled={actionLoading === u.id}
                            className="rounded border border-outline-variant bg-surface-container px-2 py-1 text-sm text-on-surface focus:border-primary focus:outline-none disabled:opacity-50"
                          >
                            <option value="free">Free</option>
                            <option value="trial">Trial</option>
                            <option value="premium">Premium</option>
                          </select>
                        </td>
                        <td className="py-4 text-sm text-on-surface-variant">
                          {/* @ts-expect-error: documents_used exists on admin response */}
                          Docs: {u.documents_used ?? 0} | Trees: {u.skill_trees_created ?? 0}
                        </td>
                        <td className="py-4">
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleResetUsage(u.id)}
                              disabled={actionLoading === u.id}
                              className="rounded p-2 text-on-surface-variant hover:bg-surface-container hover:text-primary disabled:opacity-50"
                              title="Reset usage"
                            >
                              <RefreshCw size={16} />
                            </button>
                            <button
                              onClick={() => handleDeleteUser(u.id)}
                              disabled={actionLoading === u.id || u.id === user.id}
                              className="rounded p-2 text-on-surface-variant hover:bg-error/10 hover:text-error disabled:opacity-50"
                              title="Delete user"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-between">
                  <p className="text-sm text-on-surface-variant">
                    Showing {(page - 1) * perPage + 1} to {Math.min(page * perPage, totalUsers)} of{" "}
                    {totalUsers} users
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="rounded-lg border border-outline-variant p-2 text-on-surface-variant hover:bg-surface-container disabled:opacity-50"
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="rounded-lg border border-outline-variant p-2 text-on-surface-variant hover:bg-surface-container disabled:opacity-50"
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
