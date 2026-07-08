"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { FileText, ArrowRight, Workflow, Upload, Loader2, X, File, CheckCircle, AlertCircle } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface UploadedFile {
  file: File;
  id: string;
}

type ProcessingStatus = "idle" | "uploading" | "processing" | "completed" | "failed";

export function DropZone() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [error, setError] = useState("");
  const [processingMessage, setProcessingMessage] = useState("");

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
      // Check file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        setError(`File ${file.name} exceeds 5MB limit.`);
        return;
      }
      if (validateFile(file)) {
        newFiles.push({
          file,
          id: Math.random().toString(36).substring(7),
        });
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
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const pollProcessingStatus = async (topicId: string, token: string | null): Promise<boolean> => {
    const headers: HeadersInit = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const maxAttempts = 60; // 60 attempts * 2 seconds = 2 minutes max
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const response = await fetch(`${API_URL}/ingest/${topicId}/status`, { headers });
        if (!response.ok) {
          throw new Error("Failed to check status");
        }

        const data = await response.json();

        if (data.status === "completed") {
          setProcessingMessage("Learning path generated successfully!");
          return true;
        } else if (data.status === "failed") {
          throw new Error(data.error_message || "Processing failed");
        } else if (data.status === "processing") {
          setProcessingMessage("AI is analyzing your documents...");
        } else if (data.status === "pending") {
          setProcessingMessage("Preparing to process documents...");
        }

        // Wait 2 seconds before next poll
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
    setProcessingMessage("Uploading files...");

    try {
      const formData = new FormData();
      files.forEach((f) => {
        formData.append("files", f.file);
      });

      const token = localStorage.getItem("token");
      const headers: HeadersInit = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

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

      if (!data.topic_id) {
        throw new Error("No topic ID received");
      }

      // Start polling for processing status
      setStatus("processing");
      setProcessingMessage("Processing documents with AI...");

      const success = await pollProcessingStatus(data.topic_id, token);

      if (success) {
        setStatus("completed");
        // Short delay to show success message
        await new Promise((resolve) => setTimeout(resolve, 1000));
        router.push(`/tree?topic=${data.topic_id}`);
      }
    } catch (err) {
      setStatus("failed");
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
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
      {/* Processing overlay */}
      {isProcessing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface/80 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-6 rounded-2xl border border-outline-variant bg-surface-container p-12 shadow-2xl">
            <div className="relative">
              <Loader2 size={64} className="animate-spin text-secondary" />
              <div className="absolute inset-0 animate-ping">
                <Loader2 size={64} className="text-secondary/30" />
              </div>
            </div>
            <div className="text-center">
              <h3 className="mb-2 text-xl font-semibold text-on-surface">
                {status === "uploading" ? "Uploading Files" : "Generating Learning Path"}
              </h3>
              <p className="text-on-surface-variant">{processingMessage}</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-outline">
              <div className="h-2 w-2 animate-pulse rounded-full bg-secondary" />
              <span>This may take up to a minute...</span>
            </div>
          </div>
        </div>
      )}

      {/* Success state */}
      {status === "completed" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface/80 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-4 rounded-2xl border border-outline-variant bg-surface-container p-12 shadow-2xl">
            <CheckCircle size={64} className="text-green-500" />
            <h3 className="text-xl font-semibold text-on-surface">Success!</h3>
            <p className="text-on-surface-variant">Redirecting to your learning path...</p>
          </div>
        </div>
      )}

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        className={`group relative cursor-pointer ${isDragging ? "scale-[1.02]" : ""} ${isProcessing ? "pointer-events-none opacity-50" : ""} transition-transform duration-200`}
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
          <p className="mb-6 text-body-md text-outline">Supports .pdf, .pptx, .docx (max 5MB each)</p>
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

      {/* Error message */}
      {error && (
        <div className="mt-4 flex items-center gap-2 rounded-lg bg-error/10 p-3 text-sm text-error">
          <AlertCircle size={16} />
          {error}
          {status === "failed" && (
            <button
              onClick={() => {
                setStatus("idle");
                setError("");
              }}
              className="ml-auto underline hover:no-underline"
            >
              Try again
            </button>
          )}
        </div>
      )}

      {/* File list */}
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

          {/* Upload button */}
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

      {/* Demo link when no files */}
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
