"use client";

import { useCallback, useEffect, useState } from "react";
import { AuthForm } from "@/components/AuthForm";
import { FileGallery } from "@/components/FileGallery";
import { FileUpload } from "@/components/FileUpload";
import { Button } from "@/components/ui/button";
import { isAuthenticated, logout } from "@/lib/auth";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  objectKey: string;
  uploadedAt: Date;
}

export function AuthSection() {
  const [authenticated, setAuthenticated] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

  useEffect(() => {
    setAuthenticated(isAuthenticated());
    setMounted(true);
  }, []);

  const handleLogout = useCallback(async () => {
    await logout();
    setAuthenticated(false);
    setUploadedFiles([]);
  }, []);

  const handleUploadSuccess = useCallback((file: UploadedFile) => {
    setUploadedFiles((prev) => [file, ...prev]);
  }, []);

  const handleDeleteFile = useCallback((id: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  if (!mounted) {
    return (
      <div className="w-full max-w-sm">
        <div className="h-8 w-24 bg-muted/50 rounded animate-pulse" />
        <div className="mt-8 space-y-5">
          <div className="h-10 bg-muted/30 rounded animate-pulse" />
          <div className="h-10 bg-muted/30 rounded animate-pulse" />
          <div className="h-12 bg-muted/50 rounded animate-pulse mt-4" />
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return <AuthForm onSuccess={() => setAuthenticated(true)} />;
  }

  return (
    <div className="w-full max-w-2xl space-y-8">
      {/* User bar */}
      <div className="flex items-center justify-between gap-4 animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
            <svg
              className="w-4 h-4 text-primary"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden
            >
              <title>User</title>
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <span className="text-sm text-muted-foreground">Signed in</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          className="text-muted-foreground hover:text-foreground hover:bg-transparent"
        >
          Sign out
        </Button>
      </div>

      {/* Upload section */}
      <FileUpload onUploadSuccess={handleUploadSuccess} />

      {/* File gallery */}
      {uploadedFiles.length > 0 && (
        <div className="animate-fade-up">
          <FileGallery files={uploadedFiles} onDelete={handleDeleteFile} />
        </div>
      )}
    </div>
  );
}
