"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  User as UserIcon,
  Mail,
  Calendar,
  Crown,
  FileText,
  TreeDeciduous,
  MessageSquare,
  Edit2,
  Save,
  X,
  Loader2,
  BookOpen,
  Clock,
  CheckCircle,
  AlertCircle,
  ExternalLink,
} from "lucide-react";
import { useAuth } from "../lib/auth-context";
import { userApi } from "../lib/api";
import { UsageStats, TopicSummary } from "../lib/types";
import { Header } from "../components/Header";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isLoading: authLoading, isAuthenticated, refreshUser } = useAuth();
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || "");
      userApi.getUsage().then(setUsage).catch(console.error);
      userApi.getTopics()
        .then(setTopics)
        .catch(console.error)
        .finally(() => setTopicsLoading(false));
    }
  }, [user]);

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      await userApi.updateProfile({ display_name: displayName });
      await refreshUser();
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const tierColors = {
    free: "bg-outline text-on-surface",
    trial: "bg-secondary/20 text-secondary",
    premium: "bg-tertiary/20 text-tertiary",
  };

  const formatLimit = (used: number, limit: number) => {
    if (limit === -1) return `${used} / Unlimited`;
    return `${used} / ${limit}`;
  };

  const getUsagePercent = (used: number, limit: number) => {
    if (limit === -1) return 0;
    return Math.min((used / limit) * 100, 100);
  };

  const getStatusIcon = (status: TopicSummary["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle size={16} className="text-green-500" />;
      case "processing":
        return <Loader2 size={16} className="animate-spin text-secondary" />;
      case "pending":
        return <Clock size={16} className="text-outline" />;
      case "failed":
        return <AlertCircle size={16} className="text-error" />;
    }
  };

  const getStatusLabel = (status: TopicSummary["status"]) => {
    switch (status) {
      case "completed":
        return "Completed";
      case "processing":
        return "Processing...";
      case "pending":
        return "Pending";
      case "failed":
        return "Failed";
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="relative min-h-screen bg-surface">
      <div className="pointer-events-none fixed inset-0 z-0 bg-graph-pattern opacity-20" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-surface via-surface/90 to-surface" />

      <Header />

      <main className="relative z-10 mx-auto max-w-4xl px-margin-mobile pb-16 pt-24 md:px-margin-desktop">
        <h1 className="mb-8 text-3xl font-bold text-on-surface">Profile</h1>

        {error && (
          <div className="mb-6 rounded-lg bg-error/10 p-4 text-error">{error}</div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          {/* Profile Card */}
          <div className="glass-panel rounded-xl p-6">
            <div className="mb-6 flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/20">
                  <UserIcon size={32} className="text-primary" />
                </div>
                <div>
                  {isEditing ? (
                    <input
                      type="text"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="mb-1 w-full rounded border border-outline-variant bg-surface-container px-2 py-1 text-xl font-semibold text-on-surface focus:border-primary focus:outline-none"
                      placeholder="Display name"
                    />
                  ) : (
                    <h2 className="text-xl font-semibold text-on-surface">
                      {user.display_name || "No name set"}
                    </h2>
                  )}
                  <span
                    className={`inline-block rounded-full px-3 py-1 text-xs font-medium uppercase ${tierColors[user.tier as keyof typeof tierColors]}`}
                  >
                    {user.tier}
                  </span>
                </div>
              </div>
              {isEditing ? (
                <div className="flex gap-2">
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="rounded-lg bg-tertiary p-2 text-on-primary hover:bg-tertiary/80 disabled:opacity-50"
                  >
                    {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setDisplayName(user.display_name || "");
                    }}
                    className="rounded-lg bg-surface-container p-2 text-on-surface-variant hover:bg-outline-variant"
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="rounded-lg bg-surface-container p-2 text-on-surface-variant hover:bg-outline-variant"
                >
                  <Edit2 size={16} />
                </button>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3 text-on-surface-variant">
                <Mail size={18} />
                <span>{user.email}</span>
              </div>
              <div className="flex items-center gap-3 text-on-surface-variant">
                <Calendar size={18} />
                <span>Joined {new Date(user.created_at).toLocaleDateString()}</span>
              </div>
              {user.role === "admin" && (
                <div className="flex items-center gap-3 text-tertiary">
                  <Crown size={18} />
                  <span>Administrator</span>
                </div>
              )}
            </div>

            {user.role === "admin" && (
              <Link
                href="/admin"
                className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 font-medium text-on-primary transition-colors hover:bg-primary/90"
              >
                <Crown size={18} />
                Admin Dashboard
              </Link>
            )}
          </div>

          {/* Usage Stats Card */}
          <div className="glass-panel rounded-xl p-6">
            <h3 className="mb-6 text-lg font-semibold text-on-surface">Usage This Month</h3>

            {usage ? (
              <div className="space-y-6">
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-on-surface-variant">
                      <FileText size={16} />
                      <span>Documents</span>
                    </div>
                    <span className="text-sm text-on-surface">
                      {formatLimit(usage.documents_used, usage.documents_limit)}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-surface-container">
                    <div
                      className="h-full rounded-full bg-secondary transition-all"
                      style={{
                        width: `${getUsagePercent(usage.documents_used, usage.documents_limit)}%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-on-surface-variant">
                      <TreeDeciduous size={16} />
                      <span>Skill Trees</span>
                    </div>
                    <span className="text-sm text-on-surface">
                      {formatLimit(usage.skill_trees_created, usage.skill_trees_limit)}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-surface-container">
                    <div
                      className="h-full rounded-full bg-tertiary transition-all"
                      style={{
                        width: `${getUsagePercent(usage.skill_trees_created, usage.skill_trees_limit)}%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-on-surface-variant">
                      <MessageSquare size={16} />
                      <span>Chat Messages (Today)</span>
                    </div>
                    <span className="text-sm text-on-surface">
                      {formatLimit(usage.chat_messages_today, usage.chat_messages_limit)}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-surface-container">
                    <div
                      className="h-full rounded-full bg-primary transition-all"
                      style={{
                        width: `${getUsagePercent(usage.chat_messages_today, usage.chat_messages_limit)}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="rounded-lg bg-surface-container p-4">
                  <p className="text-sm text-on-surface-variant">
                    Quizzes completed: <span className="font-semibold text-on-surface">{usage.quizzes_completed}</span>
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            )}
          </div>
        </div>

        {/* Learning Paths Section */}
        <div className="mt-8 glass-panel rounded-xl p-6">
          <div className="mb-6 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-on-surface flex items-center gap-2">
              <BookOpen size={20} className="text-secondary" />
              My Learning Paths
            </h3>
            <Link
              href="/"
              className="text-sm text-secondary hover:text-secondary/80 flex items-center gap-1"
            >
              Create New
              <ExternalLink size={14} />
            </Link>
          </div>

          {topicsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : topics.length === 0 ? (
            <div className="text-center py-12">
              <TreeDeciduous size={48} className="mx-auto mb-4 text-outline" />
              <p className="text-on-surface-variant mb-4">
                You haven&apos;t created any learning paths yet.
              </p>
              <Link
                href="/"
                className="inline-flex items-center gap-2 rounded-lg bg-tertiary px-6 py-3 font-medium text-on-primary transition-colors hover:bg-tertiary/90"
              >
                <FileText size={18} />
                Upload Documents
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {topics.map((topic) => (
                <div
                  key={topic.id}
                  className="flex items-center justify-between rounded-lg border border-outline-variant bg-surface-container p-4 transition-colors hover:border-secondary/50"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {getStatusIcon(topic.status)}
                      <h4 className="font-medium text-on-surface truncate">
                        {topic.title || "Untitled Learning Path"}
                      </h4>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-on-surface-variant">
                      <span className="flex items-center gap-1">
                        <FileText size={14} />
                        {topic.document_count} document{topic.document_count !== 1 ? "s" : ""}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar size={14} />
                        {formatDate(topic.created_at)}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-surface/50">
                        {getStatusLabel(topic.status)}
                      </span>
                    </div>
                  </div>
                  {topic.status === "completed" && (
                    <Link
                      href={`/tree?topic=${topic.id}`}
                      className="ml-4 flex items-center gap-2 rounded-lg bg-secondary/10 px-4 py-2 text-sm font-medium text-secondary transition-colors hover:bg-secondary/20"
                    >
                      <TreeDeciduous size={16} />
                      View Tree
                    </Link>
                  )}
                  {topic.status === "processing" && (
                    <span className="ml-4 text-sm text-on-surface-variant">
                      Processing...
                    </span>
                  )}
                  {topic.status === "failed" && (
                    <span className="ml-4 text-sm text-error">
                      Failed
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
