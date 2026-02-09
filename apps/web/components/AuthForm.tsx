"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { login, register } from "@/lib/auth";

type Mode = "login" | "register";

export function AuthForm({ onSuccess }: { onSuccess: () => void }) {
  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(name, email, password);
      }
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setMode(mode === "login" ? "register" : "login");
    setError(null);
  };

  return (
    <div className="w-full max-w-sm">
      {/* Mode indicator */}
      <div className="flex items-center gap-4 mb-8">
        <button
          type="button"
          onClick={() => setMode("login")}
          className={`text-sm font-medium transition-colors duration-200 ${
            mode === "login" ? "text-foreground" : "text-muted-foreground hover:text-foreground/70"
          }`}
        >
          Sign in
        </button>
        <span className="text-muted-foreground/40">/</span>
        <button
          type="button"
          onClick={() => setMode("register")}
          className={`text-sm font-medium transition-colors duration-200 ${
            mode === "register"
              ? "text-foreground"
              : "text-muted-foreground hover:text-foreground/70"
          }`}
        >
          Create account
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Name field - only for register */}
        <div
          className={`grid transition-all duration-300 ease-out ${
            mode === "register" ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
          }`}
        >
          <div className="overflow-hidden">
            <div className="pb-5">
              <label
                htmlFor="name"
                className="block text-xs uppercase tracking-wider text-muted-foreground mb-2"
              >
                Name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required={mode === "register"}
                tabIndex={mode === "register" ? 0 : -1}
                className="w-full bg-transparent border-b border-border/60 pb-2 text-foreground placeholder:text-muted-foreground/50 focus:border-primary focus:outline-none transition-colors duration-200"
                placeholder="Your name"
                autoComplete="name"
              />
            </div>
          </div>
        </div>

        {/* Email field */}
        <div>
          <label
            htmlFor="email"
            className="block text-xs uppercase tracking-wider text-muted-foreground mb-2"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full bg-transparent border-b border-border/60 pb-2 text-foreground placeholder:text-muted-foreground/50 focus:border-primary focus:outline-none transition-colors duration-200"
            placeholder="you@example.com"
            autoComplete="email"
          />
        </div>

        {/* Password field */}
        <div>
          <label
            htmlFor="password"
            className="block text-xs uppercase tracking-wider text-muted-foreground mb-2"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={mode === "register" ? 8 : undefined}
            className="w-full bg-transparent border-b border-border/60 pb-2 text-foreground placeholder:text-muted-foreground/50 focus:border-primary focus:outline-none transition-colors duration-200"
            placeholder={mode === "register" ? "At least 8 characters" : "Enter your password"}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
          />
        </div>

        {/* Error message */}
        <div
          className={`transition-all duration-300 ease-out overflow-hidden ${
            error ? "max-h-20 opacity-100" : "max-h-0 opacity-0"
          }`}
        >
          <div className="py-3 px-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        </div>

        {/* Submit button */}
        <div className="pt-4">
          <Button
            type="submit"
            disabled={loading}
            className="w-full h-12 text-sm font-medium tracking-wide uppercase bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-200 hover:shadow-lg hover:shadow-primary/20"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" aria-hidden>
                  <title>Loading</title>
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Please wait
              </span>
            ) : mode === "login" ? (
              "Sign in"
            ) : (
              "Create account"
            )}
          </Button>
        </div>
      </form>

      {/* Toggle mode link */}
      <p className="mt-6 text-sm text-muted-foreground">
        {mode === "login" ? (
          <>
            New here?{" "}
            <button
              type="button"
              onClick={toggleMode}
              className="text-primary hover:text-primary/80 transition-colors duration-200"
            >
              Create an account
            </button>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <button
              type="button"
              onClick={toggleMode}
              className="text-primary hover:text-primary/80 transition-colors duration-200"
            >
              Sign in
            </button>
          </>
        )}
      </p>
    </div>
  );
}
