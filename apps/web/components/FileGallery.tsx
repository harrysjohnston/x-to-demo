"use client";

import { useState } from "react";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  objectKey: string;
  uploadedAt: Date;
}

interface FileGalleryProps {
  files: UploadedFile[];
  onDelete?: (id: string) => void;
}

export function FileGallery({ files, onDelete }: FileGalleryProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (date: Date): string => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(date);
  };

  const getFileExtension = (name: string): string => {
    const parts = name.split(".");
    return parts.length > 1 ? parts[parts.length - 1].toUpperCase() : "FILE";
  };

  const getFileTypeColor = (type: string): string => {
    if (type.startsWith("image/")) return "bg-emerald-500/20 text-emerald-400";
    if (type.startsWith("video/")) return "bg-purple-500/20 text-purple-400";
    if (type.startsWith("audio/")) return "bg-pink-500/20 text-pink-400";
    if (type.includes("pdf")) return "bg-red-500/20 text-red-400";
    if (type.includes("zip") || type.includes("rar") || type.includes("tar"))
      return "bg-amber-500/20 text-amber-400";
    if (type.includes("json") || type.includes("javascript") || type.includes("typescript"))
      return "bg-yellow-500/20 text-yellow-400";
    return "bg-muted text-muted-foreground";
  };

  const getFileIcon = (type: string): JSX.Element => {
    if (type.startsWith("image/")) {
      return (
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth="1.5"
          aria-hidden
        >
          <title>Image</title>
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
          />
        </svg>
      );
    }
    if (type.startsWith("video/")) {
      return (
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth="1.5"
          aria-hidden
        >
          <title>Video</title>
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
          />
        </svg>
      );
    }
    if (type.startsWith("audio/")) {
      return (
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth="1.5"
          aria-hidden
        >
          <title>Audio</title>
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="m9 9 10.5-3m0 6.553v3.75a2.25 2.25 0 0 1-1.632 2.163l-1.32.377a1.803 1.803 0 1 1-.99-3.467l2.31-.66a2.25 2.25 0 0 0 1.632-2.163Zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 0 1-1.632 2.163l-1.32.377a1.803 1.803 0 1 1-.99-3.467l2.31-.66A2.25 2.25 0 0 0 9 15.553Z"
          />
        </svg>
      );
    }
    return (
      <svg
        className="w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth="1.5"
        aria-hidden
      >
        <title>File</title>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
        />
      </svg>
    );
  };

  if (files.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.15em] text-muted-foreground">
          <span className="w-6 h-px bg-border" />
          <span>Your collection</span>
        </div>
        <span className="text-xs text-muted-foreground/60">
          {files.length} {files.length === 1 ? "file" : "files"}
        </span>
      </div>

      {/* File grid */}
      <div className="grid gap-3">
        {files.map((file, index) => (
          <article
            key={file.id}
            onMouseEnter={() => setHoveredId(file.id)}
            onMouseLeave={() => setHoveredId(null)}
            className="group relative"
            style={{ animationDelay: `${index * 0.05}s` }}
          >
            <div
              className={`
                relative flex items-center gap-4 p-4 rounded-xl border border-border/60
                bg-card/50 backdrop-blur-sm
                transition-all duration-300 ease-out
                ${hoveredId === file.id ? "border-primary/40 shadow-lg shadow-primary/5 translate-x-1" : ""}
              `}
            >
              {/* File type badge */}
              <div
                className={`
                flex-shrink-0 w-12 h-12 rounded-lg flex flex-col items-center justify-center
                ${getFileTypeColor(file.type)}
                transition-transform duration-300
                ${hoveredId === file.id ? "scale-105" : ""}
              `}
              >
                {getFileIcon(file.type)}
                <span className="text-[9px] font-semibold mt-0.5 tracking-wide">
                  {getFileExtension(file.name)}
                </span>
              </div>

              {/* File info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate pr-8">{file.name}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                  <span>{formatFileSize(file.size)}</span>
                  <span className="w-1 h-1 rounded-full bg-muted-foreground/40" />
                  <span>{formatDate(file.uploadedAt)}</span>
                </div>
              </div>

              {/* Decorative corner accent */}
              <div
                className={`
                absolute top-0 right-0 w-8 h-8 overflow-hidden rounded-tr-xl
                transition-opacity duration-300
                ${hoveredId === file.id ? "opacity-100" : "opacity-0"}
              `}
              >
                <div className="absolute top-0 right-0 w-px h-4 bg-gradient-to-b from-primary/60 to-transparent" />
                <div className="absolute top-0 right-0 w-4 h-px bg-gradient-to-l from-primary/60 to-transparent" />
              </div>

              {/* Delete button */}
              {onDelete && (
                <button
                  type="button"
                  onClick={() => onDelete(file.id)}
                  className={`
                    absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg
                    text-muted-foreground hover:text-destructive hover:bg-destructive/10
                    transition-all duration-200
                    ${hoveredId === file.id ? "opacity-100" : "opacity-0"}
                  `}
                  aria-label="Delete file"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden
                  >
                    <title>Delete</title>
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
                    />
                  </svg>
                </button>
              )}
            </div>
          </article>
        ))}
      </div>

      {/* Empty state decoration */}
      <div className="flex justify-center pt-2">
        <div className="flex items-center gap-1.5">
          <div className="w-1 h-1 rounded-full bg-primary/40" />
          <div className="w-1 h-1 rounded-full bg-primary/25" />
          <div className="w-1 h-1 rounded-full bg-primary/15" />
        </div>
      </div>
    </div>
  );
}
