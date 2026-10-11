import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "00000000-0000-4000-8000-0000000000d5" }),
}));

afterEach(() => {
  cleanup();
});
