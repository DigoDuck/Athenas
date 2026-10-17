import Icon from "./Icon.jsx";

// One primary action per context. A button that can load (any `loading` prop, even false)
// always lays out its loading label (hidden), so it keeps its width when `loading` starts.
// While loading it shows `loadingLabel` and ignores clicks, so a form cannot be sent twice.
// A button without the prop reserves no room for it, so rows of links stay evenly spaced.
// A primary button with an end icon is the screen's way forward: the icon sits in an amber disc.
export default function Button({
  variant = "primary",
  type = "button",
  icon,
  iconEnd,
  loading,
  loadingLabel = "Salvando…",
  disabled = false,
  href,
  className = "",
  children,
  onClick,
  ...rest
}) {
  const classes = `ui-button ui-button--${variant} ${className}`.trim();
  const content = (
    <span className="ui-button__stack">
      <span className="ui-button__label" aria-hidden={loading || undefined}>
        {icon && <Icon name={icon} />}
        {children}
        {iconEnd && (
          <span className="ui-button__end">
            <Icon name={iconEnd} />
          </span>
        )}
      </span>
      {loading !== undefined && (
        <span className="ui-button__label ui-button__label--loading" aria-hidden={!loading || undefined}>
          <Icon name="loader" className={loading ? "ui-spin" : undefined} />
          {loadingLabel}
        </span>
      )}
    </span>
  );

  if (href && !disabled && !loading) {
    return (
      <a className={classes} href={href} onClick={onClick} {...rest}>
        {content}
      </a>
    );
  }

  return (
    <button
      className={classes}
      type={type}
      disabled={disabled}
      aria-disabled={loading || undefined}
      aria-busy={loading || undefined}
      data-loading={loading || undefined}
      onClick={loading ? (e) => e.preventDefault() : onClick}
      {...rest}
    >
      {content}
    </button>
  );
}
