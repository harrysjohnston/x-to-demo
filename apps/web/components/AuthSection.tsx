"use client";

import { useCallback, useEffect, useState } from "react";
import { AuthForm } from "@/components/AuthForm";
import { Button } from "@/components/ui/button";
import { XToDemoStudio } from "@/components/XToDemoStudio";
import { isAuthenticated, logout } from "@/lib/auth";

export function AuthSection() {
  const [authenticated, setAuthenticated] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setAuthenticated(isAuthenticated());
    setMounted(true);
  }, []);

  const handleLogout = useCallback(async () => {
    await logout();
    setAuthenticated(false);
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
    <div className="w-full max-w-6xl space-y-8">
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

      <XToDemoStudio />
    </div>
  );
}
