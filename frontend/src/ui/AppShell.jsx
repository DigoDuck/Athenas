import { useState } from "react";

import Icon from "./Icon.jsx";

// Desktop layout: 224px side navigation, flexible work area with a 32px margin.
// Below 1200px (a snapped window, for example) the navigation collapses behind a labelled button.
// items: [{ id, label, icon, href }]; `current` is the active item id.
// Routing is left to the caller: items are plain links.

export function Brand() {
  return (
    <a className="ui-brand" href="/">
      <span className="ui-brand__word">Athenas</span>
    </a>
  );
}

function NavList({ items, current }) {
  return (
    <ul className="ui-nav__list">
      {items.map((item) => (
        <li key={item.id}>
          <a
            className="ui-nav__item"
            href={item.href}
            aria-current={item.id === current ? "page" : undefined}
          >
            <Icon name={item.icon} size={24} />
            {item.label}
          </a>
        </li>
      ))}
    </ul>
  );
}

export default function AppShell({ items, secondaryItems = [], current, aside, children }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="ui-shell" data-nav-open={open ? "true" : undefined}>
      <a className="ui-skip-link" href="#conteudo">
        Ir para o conteúdo
      </a>
      <header className="ui-shell__bar" data-print="hide">
        <button
          type="button"
          className="ui-shell__menu-button"
          aria-expanded={open}
          aria-controls="navegacao-principal"
          onClick={() => setOpen(!open)}
        >
          <Icon name={open ? "close" : "menu"} size={24} />
          Menu
        </button>
        <Brand />
      </header>
      {/* The column carries the background so it reaches the bottom of long pages;
          the nav inside stays in view while the page scrolls. */}
      <div className="ui-shell__nav-column" data-print="hide">
        <nav className="ui-nav" id="navegacao-principal" aria-label="Principal">
          <div className="ui-nav__brand">
            <Brand />
          </div>
          <NavList items={items} current={current} />
          {secondaryItems.length > 0 && (
            <div className="ui-nav__secondary">
              <NavList items={secondaryItems} current={current} />
            </div>
          )}
        </nav>
      </div>
      <main className="ui-shell__main" id="conteudo" tabIndex={-1}>
        <div className="ui-shell__content">{children}</div>
      </main>
      {aside && (
        <aside className="ui-shell__aside" data-print="hide">
          {aside}
        </aside>
      )}
    </div>
  );
}
