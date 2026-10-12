import { useEffect, useState } from "react";

import Library from "./pages/Library.jsx";
import Roadmap from "./pages/Roadmap.jsx";
import { AppShell } from "./ui/index.js";

const PAGES = {
  roadmap: { label: "Roadmap", icon: "roadmap", Component: Roadmap },
  biblioteca: { label: "Biblioteca", icon: "library", Component: Library },
};

const NAV_ITEMS = Object.entries(PAGES).map(([id, { label, icon }]) => ({
  id,
  label,
  icon,
  href: `#/${id}`,
}));

function currentPage() {
  const key = window.location.hash.replace("#/", "");
  return key in PAGES ? key : "roadmap";
}

export default function App() {
  const [page, setPage] = useState(currentPage);

  useEffect(() => {
    const onHashChange = () => setPage(currentPage());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const { Component } = PAGES[page];

  return (
    <AppShell items={NAV_ITEMS} current={page}>
      <Component />
    </AppShell>
  );
}
