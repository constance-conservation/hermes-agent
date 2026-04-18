# Hermes architecture diagrams (exportable)

| # | Asset | Purpose |
|---|--------|--------|
| | [hermes-memory-architecture.md](hermes-memory-architecture.md) | All three diagrams in one Markdown file; **embeds PNG** and includes Mermaid source. |
| | [hermes-memory-architecture.agent.json](hermes-memory-architecture.agent.json) | **Machine-readable** architecture spec for tools and coding agents (paths, pipeline, layers, code index). |
| **1** | [01-hermes-memory-turn-flow.png](01-hermes-memory-turn-flow.png) | Diagram A — full turn (raster). |
| **2** | [02-hermes-memory-cortical-lattice.png](02-hermes-memory-cortical-lattice.png) | Diagram B — cortical lattice (raster). |
| **3** | [03-hermes-memory-external-products.png](03-hermes-memory-external-products.png) | Diagram C — external products (raster). |
| | [hermes-memory-turn-flow.mmd](hermes-memory-turn-flow.mmd) | Diagram A — Mermaid source. |
| | [hermes-memory-cortical-lattice.mmd](hermes-memory-cortical-lattice.mmd) | Diagram B — Mermaid source. |
| | [hermes-memory-external-products.mmd](hermes-memory-external-products.mmd) | Diagram C — Mermaid source. |

## Regenerate PNG (Mermaid CLI)

From this directory:

```bash
cd docs/diagrams
npx -y @mermaid-js/mermaid-cli -i hermes-memory-turn-flow.mmd -o 01-hermes-memory-turn-flow.png -w 2400 -H 1800
npx -y @mermaid-js/mermaid-cli -i hermes-memory-cortical-lattice.mmd -o 02-hermes-memory-cortical-lattice.png -w 2400 -H 1200
npx -y @mermaid-js/mermaid-cli -i hermes-memory-external-products.mmd -o 03-hermes-memory-external-products.png -w 2000 -H 1400
```

## Export to PDF

Open the PNG in Preview (or any viewer) and print/save as PDF, or embed the PNG in a document.

## GitHub

The fenced `mermaid` blocks in `hermes-memory-architecture.md` also render on github.com when viewing the file.
