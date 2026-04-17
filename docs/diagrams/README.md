# Hermes architecture diagrams (exportable)

| Asset | Purpose |
|--------|--------|
| [hermes-memory-architecture.md](hermes-memory-architecture.md) | All three diagrams in one Markdown file; **embeds PNG** and includes Mermaid source. |
| `*.png` / `*.svg` | **Pre-rendered images** for each diagram (open directly or embed). |
| [hermes-memory-turn-flow.mmd](hermes-memory-turn-flow.mmd) | Diagram A — Mermaid source. |
| [hermes-memory-cortical-lattice.mmd](hermes-memory-cortical-lattice.mmd) | Diagram B — Mermaid source. |
| [hermes-memory-external-products.mmd](hermes-memory-external-products.mmd) | Diagram C — Mermaid source. |

**Image files:** `hermes-memory-turn-flow.{png,svg}`, `hermes-memory-cortical-lattice.{png,svg}`, `hermes-memory-external-products.{png,svg}`.

## Export to SVG or PNG (Mermaid CLI)

From this directory:

```bash
cd docs/diagrams
npx -y @mermaid-js/mermaid-cli -i hermes-memory-turn-flow.mmd -o hermes-memory-turn-flow.svg
npx -y @mermaid-js/mermaid-cli -i hermes-memory-cortical-lattice.mmd -o hermes-memory-cortical-lattice.svg
npx -y @mermaid-js/mermaid-cli -i hermes-memory-external-products.mmd -o hermes-memory-external-products.svg
```

PNG:

```bash
npx -y @mermaid-js/mermaid-cli -i hermes-memory-turn-flow.mmd -o hermes-memory-turn-flow.png -w 2400
```

## Export to PDF

- **Via SVG:** generate SVG as above, then open in a browser or Inkscape and print/save as PDF.
- **Via Markdown:** open `hermes-memory-architecture.md` in VS Code with a Markdown PDF extension, or use Pandoc with a Mermaid filter if your toolchain supports it.

## GitHub

The fenced `mermaid` blocks in `hermes-memory-architecture.md` render on github.com when viewing the file.
