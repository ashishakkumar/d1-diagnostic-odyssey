import path from "node:path";
import { defineConfig } from "vitest/config";

const webModules = path.resolve(__dirname, "node_modules");

function pkg(name: string): string {
  return path.join(webModules, name);
}

export default defineConfig({
  esbuild: {
    jsx: "automatic",
  },
  server: {
    fs: {
      allow: [path.resolve(__dirname, "../.."), webModules],
    },
  },
  test: {
    environment: "jsdom",
    include: [path.resolve(__dirname, "../../tests/web/**/*.test.tsx")],
    setupFiles: ["./vitest.setup.ts"],
  },
  resolve: {
    alias: [
      { find: "@", replacement: path.resolve(__dirname) },
      { find: "@testing-library/jest-dom/vitest", replacement: pkg("@testing-library/jest-dom/vitest") },
      { find: "@testing-library/react", replacement: pkg("@testing-library/react") },
      { find: "@testing-library/user-event", replacement: pkg("@testing-library/user-event") },
      { find: /^react(\/.*)?$/, replacement: `${pkg("react")}$1` },
      { find: /^react-dom(\/.*)?$/, replacement: `${pkg("react-dom")}$1` },
      { find: "vitest", replacement: pkg("vitest") },
    ],
  },
});
