import { useEffect, useState } from "react";

import Organization from "./pages/Organization.jsx";
import Roadmap from "./pages/Roadmap.jsx";

const PAGES = {
  organizacao: { label: "Organização", Component: Organization },
  roadmap: { label: "Roadmap", Component: Roadmap },
};

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
    <>
      <header className="topbar">
        <strong>Athenas</strong>
        <nav>
          {Object.entries(PAGES).map(([key, { label }]) => (
            <a key={key} href={`#/${key}`} aria-current={key === page ? "page" : undefined}>
              {label}
            </a>
          ))}
        </nav>
      </header>
      <main>
        <Component />
      </main>
    </>
  );
}
