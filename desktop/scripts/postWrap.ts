/**
 * Electrobun postWrap hook — placeholder.
 *
 * Python runtime is now bundled via the `copy` config in electrobun.config.ts,
 * which places it inside the inner app bundle before compression. This ensures
 * it survives Electrobun's self-extraction (which replaces the entire Contents/
 * directory of the outer wrapper on first launch).
 */

console.log("postWrap: no-op (Python is bundled via copy config)");
