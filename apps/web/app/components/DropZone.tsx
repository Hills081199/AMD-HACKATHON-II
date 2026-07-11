"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  ArrowRight,
  Workflow,
  Upload,
  X,
  File,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Ordered pipeline steps shown to the user
const PIPELINE_STEPS = [
  { key: "chunking",   label: "Chunking documents",           icon: "📄" },
  { key: "extracting", label: "Extracting concepts",           icon: "🧠" },
  { key: "clustering", label: "Clustering & deduplicating",    icon: "🔗" },
  { key: "inferring",  label: "Inferring prerequisites",       icon: "🔍" },
  { key: "validating", label: "Validating dependency graph",   icon: "✅" },
  { key: "leveling",   label: "Assigning concept tiers",       icon: "🏗️" },
  { key: "building",   label: "Assembling learning tree",      icon: "🛠️" },
];

function stepIndexFromLabel(currentStep: string | null): number {
  if (!currentStep) return -1;
  const lower = currentStep.toLowerCase();
  // Match by key word contained in the backend label string
  const idx = PIPELINE_STEPS.findIndex((s) => lower.includes(s.key));
  if (idx !== -1) return idx;
  // Fallback: match by first word of step label
  return PIPELINE_STEPS.findIndex((s) =>
    lower.includes(s.label.toLowerCase().split(" ")[0])
  );
}

interface UploadedFile {
  file: File;
  id: string;
}

type ProcessingStatus = "idle" | "uploading" | "processing" | "completed" | "failed";

// ── Animated Spinner ─────────────────────────────────────────────────────────
function PipelineLoader({
  currentStep,
  status,
}: {
  currentStep: string | null;
  status: ProcessingStatus;
}) {
  const activeIndex = stepIndexFromLabel(currentStep);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface/85 backdrop-blur-md">
      <div className="relative flex w-full max-w-md flex-col items-center gap-8 rounded-2xl border border-white/10 bg-surface-container p-10 shadow-2xl">
        {/* Glowing ring spinner */}
        <div className="relative flex items-center justify-center">
          {/* Outer pulsing glow */}
          <span className="absolute h-28 w-28 animate-ping rounded-full bg-secondary/20" />
          {/* Spinning ring */}
          <span
            className="absolute h-24 w-24 rounded-full border-4 border-transparent animate-spin"
            style={{
              borderTopColor: "#4cd7f6",
              borderRightColor: "rgba(76,215,246,0.3)",
            }}
          />
          {/* Inner icon */}
          <div className="flex h-16 w-16 items-center justify-center rounded-full border border-white/10 bg-surface text-3xl shadow-inner">
            {status === "uploading" ? "⬆️" : currentStep ? (
              PIPELINE_STEPS.find((s) => currentStep.includes(s.key))?.icon ?? "⚙️"
            ) : "⚙️"}
          </div>
        </div>

        {/* Title */}
        <div className="text-center">
          <h3 className="mb-1 text-lg font-semibold text-on-surface">
            {status === "uploading" ? "Uploading Files…" : "Generating Learning Path"}
          </h3>
          <p className="text-sm text-on-surface-variant">
            {currentStep ?? (status === "uploading" ? "Uploading files to server…" : "Starting pipeline…")}
          </p>
        </div>

        {/* Step progress bar */}
        {status === "processing" && (
          <div className="w-full">
            <div className="mb-3 flex items-center justify-between text-xs text-outline">
              <span>Step {Math.max(activeIndex + 1, 1)} of {PIPELINE_STEPS.length}</span>
              <span>{Math.round(Math.max(activeIndex + 1, 1) / PIPELINE_STEPS.length * 100)}%</span>
            </div>
            {/* Overall progress bar */}
            <div className="mb-4 h-1.5 w-full overflow-hidden rounded-full bg-surface-container-high">
              <div
                className="h-full rounded-full bg-secondary transition-all duration-700"
                style={{
                  width: `${Math.round(Math.max(activeIndex + 1, 1) / PIPELINE_STEPS.length * 100)}%`,
                }}
              />
            </div>

            {/* Step dots */}
            <div className="flex flex-col gap-1.5">
              {PIPELINE_STEPS.map((step, idx) => {
                const state =
                  idx < activeIndex
                    ? "done"
                    : idx === activeIndex
                    ? "active"
                    : "pending";
                return (
                  <div
                    key={step.key}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-xs transition-all duration-300 ${
                      state === "active"
                        ? "bg-secondary/15 text-secondary"
                        : state === "done"
                        ? "text-tertiary/80"
                        : "text-on-surface-variant/30"
                    }`}
                  >
                    <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] transition-all ${
                      state === "active"
                        ? "animate-pulse bg-secondary text-black font-bold"
                        : state === "done"
                        ? "bg-tertiary/30 text-tertiary"
                        : "border border-white/10 text-outline/30"
                    }`}>
                      {state === "done" ? "✓" : idx + 1}
                    </span>
                    <span className="leading-none">{step.icon} {step.label}</span>
                    {state === "active" && (
                      <span className="ml-auto flex gap-0.5">
                        {[0, 1, 2].map((i) => (
                          <span
                            key={i}
                            className="h-1 w-1 rounded-full bg-secondary animate-bounce"
                            style={{ animationDelay: `${i * 150}ms` }}
                          />
                        ))}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <p className="text-center text-xs text-outline">
          This may take 30 seconds to a few minutes…
        </p>
      </div>
    </div>
  );
}

// ── Main DropZone ─────────────────────────────────────────────────────────────
export function DropZone() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [error, setError] = useState("");
  const [currentStep, setCurrentStep] = useState<string | null>(null);

  const acceptedTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ];

  const acceptedExtensions = [".pdf", ".pptx", ".docx"];

  const validateFile = (file: File): boolean => {
    const extension = "." + file.name.split(".").pop()?.toLowerCase();
    return acceptedTypes.includes(file.type) || acceptedExtensions.includes(extension);
  };

  const handleFiles = useCallback((fileList: FileList | null) => {
    if (!fileList) return;
    setError("");
    const newFiles: UploadedFile[] = [];
    Array.from(fileList).forEach((file) => {
      if (file.size > 5 * 1024 * 1024) {
        setError(`File ${file.name} exceeds 5 MB limit.`);
        return;
      }
      if (validateFile(file)) {
        newFiles.push({ file, id: Math.random().toString(36).substring(7) });
      } else {
        setError(`Invalid file type: ${file.name}. Only PDF, PPTX, and DOCX are supported.`);
      }
    });
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const pollProcessingStatus = async (topicId: string, token: string | null): Promise<boolean> => {
    const headers: HeadersInit = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const maxAttempts = 120; // 4 minutes max
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const response = await fetch(`${API_URL}/ingest/${topicId}/status`, { headers });
        if (!response.ok) throw new Error("Failed to check status");

        const data = await response.json();

        if (data.status === "completed") {
          setCurrentStep("🎉 Pipeline complete!");
          return true;
        } else if (data.status === "failed") {
          throw new Error(data.error_message || "Processing failed");
        } else {
          // Show current step label from backend
          if (data.current_step) {
            setCurrentStep(data.current_step);
          }
        }

        await new Promise((resolve) => setTimeout(resolve, 2000));
        attempts++;
      } catch (err) {
        throw err;
      }
    }

    throw new Error("Processing timed out. Please try again.");
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      router.push("/tree");
      return;
    }

    setStatus("uploading");
    setError("");
    setCurrentStep(null);

    try {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f.file));

      const token = localStorage.getItem("token");
      const headers: HeadersInit = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const response = await fetch(`${API_URL}/ingest`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Upload failed");
      }

      const data = await response.json();
      if (!data.topic_id) throw new Error("No topic ID received");

      setStatus("processing");
      setCurrentStep("📄 Chunking documents…");

      const success = await pollProcessingStatus(data.topic_id, token);

      if (success) {
        setStatus("completed");
        await new Promise((resolve) => setTimeout(resolve, 1200));
        router.push(`/tree?topic=${data.topic_id}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Upload failed. Please try again.";

      if (errorMessage.toLowerCase().includes("timeout") || errorMessage.toLowerCase().includes("timed out")) {
        setStatus("idle");
        setCurrentStep(null);
        setError("Processing is taking longer than expected. Your documents are being processed in the background. Check your Profile page for status updates.");
        setFiles([]);
        return;
      }

      setStatus("failed");
      setError(errorMessage);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const isProcessing = status === "uploading" || status === "processing";

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* ── Pipeline loading overlay ── */}
      {isProcessing && (
        <PipelineLoader currentStep={currentStep} status={status} />
      )}

      {/* ── Success overlay ── */}
      {status === "completed" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface/85 backdrop-blur-md">
          <div className="flex flex-col items-center gap-4 rounded-2xl border border-white/10 bg-surface-container p-12 shadow-2xl">
            <div className="relative">
              <CheckCircle size={72} className="text-green-400" />
              <span className="absolute inset-0 animate-ping rounded-full bg-green-400/20" />
            </div>
            <h3 className="text-xl font-semibold text-on-surface">Success!</h3>
            <p className="text-on-surface-variant">Redirecting to your learning path…</p>
          </div>
        </div>
      )}

      {/* ── Drop zone ── */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        className={`group relative cursor-pointer ${isDragging ? "scale-[1.02]" : ""} ${
          isProcessing ? "pointer-events-none opacity-50" : ""
        } transition-transform duration-200`}
      >
        <div
          className={`pointer-events-none absolute inset-0 rounded-xl blur-xl transition-opacity duration-500 ${
            isDragging ? "bg-secondary/20 opacity-100" : "bg-secondary/10 opacity-0 group-hover:opacity-100"
          }`}
        />
        <div
          className={`glass-panel glow-active relative z-10 flex min-h-[300px] flex-col items-center justify-center rounded-xl border border-dashed p-12 transition-colors duration-300 ${
            isDragging
              ? "border-secondary bg-secondary/5"
              : "border-outline-variant group-hover:border-secondary"
          }`}
        >
          <div
            className={`mb-8 flex items-center justify-center gap-6 transition-colors duration-300 ${
              isDragging ? "text-secondary" : "text-on-surface-variant group-hover:text-secondary"
            }`}
          >
            <FileText size={44} strokeWidth={1.5} />
            <ArrowRight size={28} strokeWidth={1.5} />
            <Workflow size={44} strokeWidth={1.5} />
          </div>
          <h3 className="mb-2 text-headline-lg-mobile text-on-surface">
            {isDragging ? "Drop Files Here" : "Drag & Drop Files Here"}
          </h3>
          <p className="mb-6 text-body-md text-outline">Supports .pdf, .pptx, .docx (max 5 MB each)</p>
          <span className="flex items-center gap-2 rounded bg-primary px-8 py-3 text-label-caps text-on-primary shadow-sm transition-colors group-hover:bg-primary-container">
            <Upload size={16} />
            BROWSE FILES
          </span>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.pptx,.docx"
          multiple
          onChange={handleInputChange}
          className="hidden"
          disabled={isProcessing}
        />
      </div>

      {/* ── Error/Info message ── */}
      {error && (
        <div className={`mt-4 flex items-start gap-2 rounded-lg p-3 text-sm ${
          error.includes("background") ? "bg-secondary/10 text-secondary" : "bg-error/10 text-error"
        }`}>
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <div className="flex-1">
            {error}
            {error.includes("Profile") && (
              <button
                onClick={() => router.push("/profile")}
                className="ml-2 font-medium underline hover:no-underline"
              >
                Go to Profile →
              </button>
            )}
          </div>
          {status === "failed" && (
            <button
              onClick={() => {
                setStatus("idle");
                setError("");
                setCurrentStep(null);
              }}
              className="shrink-0 underline hover:no-underline"
            >
              Try again
            </button>
          )}
          {status === "idle" && error.includes("background") && (
            <button
              onClick={() => setError("")}
              className="shrink-0 text-secondary/60 hover:text-secondary"
            >
              <X size={16} />
            </button>
          )}
        </div>
      )}

      {/* ── File list ── */}
      {files.length > 0 && !isProcessing && status !== "completed" && (
        <div className="mt-6 space-y-3">
          <h4 className="text-sm font-medium text-on-surface-variant">
            Selected Files ({files.length})
          </h4>
          {files.map((f) => (
            <div
              key={f.id}
              className="flex items-center justify-between rounded-lg border border-outline-variant bg-surface-container p-3"
            >
              <div className="flex items-center gap-3">
                <File size={20} className="text-secondary" />
                <div>
                  <p className="text-sm font-medium text-on-surface">{f.file.name}</p>
                  <p className="text-xs text-on-surface-variant">{formatFileSize(f.file.size)}</p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(f.id);
                }}
                className="rounded p-1 text-on-surface-variant hover:bg-error/10 hover:text-error"
              >
                <X size={16} />
              </button>
            </div>
          ))}

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleUpload();
            }}
            disabled={isProcessing}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-tertiary px-6 py-3 font-medium text-on-primary transition-colors hover:bg-tertiary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Workflow size={20} />
            Generate Learning Path
          </button>
        </div>
      )}

      {/* ── Demo link ── */}
      {files.length === 0 && !isProcessing && (
        <p className="mt-4 text-center text-stats-mono text-outline">
          Or{" "}
          <button
            onClick={() => router.push("/tree")}
            className="text-secondary underline hover:text-secondary/80"
          >
            try the demo mastery tree
          </button>
        </p>
      )}
    </div>
  );
}
