import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "./page";

describe("HomePage", () => {
  it("renders without crashing", () => {
    render(<HomePage />);
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("displays the app title", () => {
    render(<HomePage />);
    expect(screen.getByText("input X")).toBeInTheDocument();
    expect(screen.getByText(/runnable demo code spec/i)).toBeInTheDocument();
  });

  it("displays the description text", () => {
    render(<HomePage />);
    expect(screen.getByText(/Upload or paste brainstorming input/i)).toBeInTheDocument();
  });

  it("renders the auth buttons", () => {
    render(<HomePage />);
    // There are multiple "Sign in" buttons, so use getAllByText
    expect(screen.getAllByText("Sign in").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Create account").length).toBeGreaterThan(0);
  });
});
