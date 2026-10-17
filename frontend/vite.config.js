import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Library build: one ESM file; React and the Plugboard SDK stay bare imports
// that the host's import map resolves to its own instances.
export default defineConfig({
  plugins: [react()],
  build: {
    lib: { entry: "src/index.jsx", formats: ["es"], fileName: () => "starter.js" },
    outDir: "../plugboard_starter/static",
    emptyOutDir: true,
    rollupOptions: { external: ["react", "react-dom", "react/jsx-runtime", "react-dom/client", "@plugboard/sdk"] },
  },
});
