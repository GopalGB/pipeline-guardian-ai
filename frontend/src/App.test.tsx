import { render, screen } from "@testing-library/react";
import { vi, it, expect } from "vitest";
import App from "./App";
vi.mock("./api", () => ({ listIncidents: vi.fn().mockResolvedValue([]), decide: vi.fn(), retry: vi.fn() }));
it("renders an accessible empty operator state", async () => { render(<App />); expect(await screen.findByText("No incidents require attention.")).toBeInTheDocument(); });
