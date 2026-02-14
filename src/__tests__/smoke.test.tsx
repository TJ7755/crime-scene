import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "../App";

describe("App smoke test", () => {
  it("renders case header and an action button", async () => {
    render(<App />);
    expect(await screen.findByText(/Case ID/i)).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /Remove Evidence/i })).toBeInTheDocument();
  });
});
