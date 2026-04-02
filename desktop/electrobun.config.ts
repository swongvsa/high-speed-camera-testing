import type { ElectrobunConfig } from "electrobun";
import { join } from "path";

// import.meta.dir is the desktop/ directory at build time.
// One level up is the repo root where main.py lives.
const devRepoRoot = join(import.meta.dir, "..");

export default {
  app: {
    name: "High Speed Camera",
    identifier: "com.internal.highspeedcamera",
    version: "1.0.0",
  },
  build: {
    bun: {
      entrypoint: "src/bun/index.ts",
    },
    copy: {
      // Splash screen HTML served via views:// scheme
      "src/splash/index.html": "views/splash/index.html",
      // Main UI served via views:// scheme (replaces Gradio)
      "../src/ui/web": "views/main",
      // Bundle the entire Python runtime + app into the inner app bundle
      // so it survives Electrobun's self-extraction (which replaces Contents/).
      "build/python": "python",
    },
  },
  scripts: {
    // Copies build/python/ into .app/Contents/Resources/python/ so the
    // packaged app can find and spawn the bundled Python runtime.
    postWrap: "./scripts/postWrap.ts",
  },
  runtime: {
    // Baked in at build time so index.ts can locate main.py in dev mode.
    // In a production bundle the Python tree is under RESOURCES_FOLDER instead.
    devRepoRoot,
  },
  // No release.baseUrl — internal tool, no auto-update required
} satisfies ElectrobunConfig;
