import { useState } from "react";

import emblem from "../assets/brand/athenas-emblem.svg";
import Icon from "./Icon.jsx";

// Desktop layout: 224px side navigation, flexible work area with a 32px margin.
// Below 1200px (a snapped window, for example) the navigation collapses behind a labelled button.
// items: [{ id, label, icon, href }]; `current` is the active item id.
// Routing is left to the caller: items are plain links.
//
// `scene="home"` puts the sunset panorama behind the whole screen, for the screens that open
// the day (Início, Roadmap). It is decorative and disappears in focus mode and in print. Its
// left side fades to marble: only the navigation and the page's opening lines sit there, and
// everything else on the page goes on an opaque Panel. Without a scene (default) the page sits
// on the marble background.

// The owl emblem with the wordmark. The image is decorative: the wordmark names the link.
// `compact` puts them side by side, for the collapsed top bar.
export function Brand({ compact = false }) {
  return (
    <a className={`ui-brand${compact ? " ui-brand--compact" : ""}`} href="/">
      <img className="ui-brand__emblem" src={emblem} alt="" width={compact ? 32 : 56} height={compact ? 32 : 56} />
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

export default function AppShell({
  items,
  secondaryItems = [],
  current,
  aside,
  scene = null,
  children,
}) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="ui-shell"
      data-nav-open={open ? "true" : undefined}
      data-scene={scene || undefined}
    >
      {scene && <div className={`ui-shell__scene ui-shell__scene--${scene} decor`} aria-hidden="true" />}
      {/* The hash is the app's router, so the skip link moves focus without changing the URL. */}
      <a
        className="ui-skip-link"
        href="#conteudo"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("conteudo")?.focus();
        }}
      >
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
        <Brand compact />
      </header>
      {/* The column carries the background so it reaches the bottom of long pages;
          the nav inside stays in view while the page scrolls. */}
      <div className="ui-shell__nav-column" data-print="hide">
        {/* Following a link closes the collapsed menu, so the new page is not pushed down. */}
        <nav className="ui-nav" id="navegacao-principal" aria-label="Principal" onClick={() => setOpen(false)}>
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
