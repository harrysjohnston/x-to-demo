"use client";

import { useCallback, useId, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { type UploadInstruction, uploadFile } from "@/lib/upload";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  objectKey: string;
  uploadedAt: Date;
}

interface FileUploadProps {
  onUploadSuccess?: (file: UploadedFile) => void;
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();

  const handleFileSelect = useCallback((selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setProgress(0);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

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

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        handleFileSelect(droppedFile);
      }
    },
    [handleFileSelect],
  );

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file");
      return;
    }

    setUploading(true);
    setError(null);
    setProgress(0);

    try {
      // Step 1: Request presigned upload URL from API
      const instruction = await api.post<UploadInstruction>("/uploads/", {
        filename: file.name,
        content_type: file.type || "application/octet-stream",
        size_bytes: file.size,
      });

      // Step 2: Upload file directly to storage
      await uploadFile(instruction, file, (percent) => {
        setProgress(percent);
      });

      setProgress(100);

      // Notify parent of successful upload
      if (onUploadSuccess) {
        onUploadSuccess({
          id: crypto.randomUUID(),
          name: file.name,
          size: file.size,
          type: file.type || "application/octet-stream",
          objectKey: instruction.objectKey,
          uploadedAt: new Date(),
        });
      }

      // Reset after short delay to show completion
      setTimeout(() => {
        setFile(null);
        setProgress(0);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }, 1000);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setError(message);
      setProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (type: string): JSX.Element => {
    if (type.startsWith("image/")) {
      return (
        <svg
          className="w-5 h-5"
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
    return (
      <svg
        className="w-5 h-5"
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

  return (
    <div className="w-full">
      {/* Drop zone */}
      <label
        htmlFor={inputId}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          block w-full text-left relative cursor-pointer rounded-xl border-2 border-dashed transition-all duration-300
          ${
            isDragging
              ? "border-primary bg-primary/5 scale-[1.02]"
              : "border-border/60 hover:border-primary/50 hover:bg-card/50"
          }
          ${uploading ? "pointer-events-none opacity-70" : ""}
        `}
      >
        <input
          id={inputId}
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          disabled={uploading}
          className="hidden"
        />

        <div className="p-8 text-center">
          {!file ? (
            <>
              <div
                className={`
                mx-auto w-12 h-12 rounded-full bg-muted/50 flex items-center justify-center mb-4
                transition-transform duration-300
                ${isDragging ? "scale-110 bg-primary/20" : ""}
              `}
              >
                <svg
                  className={`w-6 h-6 transition-colors ${isDragging ? "text-primary" : "text-muted-foreground"}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  aria-hidden
                >
                  <title>Upload</title>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
                  />
                </svg>
              </div>
              <p className="text-sm text-muted-foreground">
                <span className="text-foreground font-medium">Drop a file here</span> or click to
                browse
              </p>
              <p className="text-xs text-muted-foreground/60 mt-1">Any file type accepted</p>
            </>
          ) : (
            <div className="flex items-center gap-4 text-left">
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                {getFileIcon(file.type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
              </div>
              {!uploading && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  className="flex-shrink-0 p-1 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden
                  >
                    <title>Clear</title>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Progress overlay */}
        {uploading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 rounded-xl">
            <div className="text-center">
              {/* Circular progress */}
              <div className="relative w-16 h-16 mx-auto mb-3">
                <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64" aria-hidden>
                  <title>Upload progress</title>
                  <circle
                    className="text-muted/30"
                    strokeWidth="4"
                    stroke="currentColor"
                    fill="transparent"
                    r="28"
                    cx="32"
                    cy="32"
                  />
                  <circle
                    className="text-primary transition-all duration-300"
                    strokeWidth="4"
                    strokeDasharray={175.93}
                    strokeDashoffset={175.93 - (progress / 100) * 175.93}
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="transparent"
                    r="28"
                    cx="32"
                    cy="32"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-sm font-medium">
                  {progress}%
                </span>
              </div>
              <p className="text-xs text-muted-foreground">Uploading...</p>
            </div>
          </div>
        )}
      </label>

      {/* Error message */}
      {error && (
        <div className="mt-4 py-3 px-4 bg-destructive/10 border border-destructive/20 rounded-lg animate-scale-in">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Upload button */}
      {file && !uploading && (
        <div className="mt-4 animate-fade-up">
          <Button
            onClick={handleUpload}
            className="w-full h-11 text-sm font-medium tracking-wide uppercase bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-200 hover:shadow-lg hover:shadow-primary/20"
          >
            Upload file
          </Button>
        </div>
      )}
    </div>
  );
}
