import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";

// The base styles load before the screens, so a screen's own class can override a component's.
import "./styles/fonts.css";
import "./styles/tokens.css";
import "./styles/base.css";
import "./ui/ui.css";
import App from "./App.jsx";

// Component showcase, dev mode only: open /#design.
const Showcase = import.meta.env.DEV ? lazy(() => import("./design/Showcase.jsx")) : null;
const Root = Showcase && window.location.hash === "#design" ? Showcase : App;

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <Suspense>
      <Root />
    </Suspense>
  </StrictMode>,
);
