# vendor/

Third-party assets bundled once, off-band, so a single `docs-site-macos` generation never
runs a build step or hits the network.

## beautiful-mermaid.min.js

- Source: `github.com/lukilabs/beautiful-mermaid`, npm `beautiful-mermaid@1.1.3`, MIT license.
- Built with: `esbuild entry.mjs --bundle --format=iife --global-name=BeautifulMermaid --minify --outfile=beautiful-mermaid.min.js`
  where `entry.mjs` re-exports `renderMermaidSVG`/`renderMermaidSVGAsync`. The published package
  ships `dist/index.js` as ESM with two bare imports (`entities`, `elkjs/lib/elk.bundled.js`) that
  cannot run in a plain `<script>` without this bundling step.
- Exposes `window.BeautifulMermaid.renderMermaidSVG(dsl, opts)` once loaded — synchronous, no
  `await` needed.
- **Known upstream behavior to work around**: every call to `renderMermaidSVG()` hard-codes a
  `@import url('https://fonts.googleapis.com/...')` into the returned SVG's `<style>` block, with
  no API option to disable it. This violates docs-site-macos's Self-Contained rule if left in —
  the "Mermaid Diagram Engine" section of `SKILL.md` strips it via regex immediately after render.
  Font falls back to the system stack already declared after `'Inter'` in the same style block.
- To rebuild after a version bump: `npm install beautiful-mermaid@<version>`, write the same
  `entry.mjs`, re-run the `esbuild` command above, replace this file, update the version note here.

Re-verify the Self-Contained property after any rebuild: grep the rendered output SVG for
`https://` — the only match should be the `http://www.w3.org/2000/svg` XML namespace, never a
`fonts.googleapis.com` (or other) network URL.
