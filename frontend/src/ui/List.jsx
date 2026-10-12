// Rows with separators: the default for the library and reviews.
export function List({ label, children }) {
  return (
    <ul className="ui-list" aria-label={label}>
      {children}
    </ul>
  );
}

// title, meta and badges on the left; the next action on the right.
export function ListRow({ title, href, meta, badges, action }) {
  return (
    <li className="ui-list__row">
      <div className="ui-list__main">
        {href ? (
          <a className="ui-list__title" href={href}>
            {title}
          </a>
        ) : (
          <span className="ui-list__title">{title}</span>
        )}
        {meta && <span className="t-meta">{meta}</span>}
      </div>
      {badges && <div className="ui-list__badges">{badges}</div>}
      {action && <div className="ui-list__action">{action}</div>}
    </li>
  );
}
