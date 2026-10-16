---
paths:
  - "frontend/**"
---

# Frontend rules

- Invoke `impeccable` before any change that alters pixels. It reads `PRODUCT.md`,
  `docs/design-system.md` and `src/styles/tokens.css`.
- Colors, spacing, radius and type only through the variables in `src/styles/tokens.css`, never
  raw values in a screen.
- Reuse `src/ui/` (import from `src/ui/index.js`). A new base component goes there and shows up in
  `/#design`.
- UI copy in pt-BR. Terms from the Markdown contract (spec 4.1) stay exactly as written.
- No new npm dependency without Diogo's ok. There is no router and no state library: navigation is
  the hash map in `src/App.jsx`.
- Check a changed screen in the browser at 1440x900 before calling it done. `make lint` runs
  eslint.
