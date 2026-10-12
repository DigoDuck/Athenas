import Icon from "./Icon.jsx";

// One primary action per context. The loading label is always laid out (hidden), so the
// button keeps its width when `loading` starts. While loading it
// shows `loadingLabel` and ignores clicks, so a form cannot be sent twice.
export default function Button({
  variant = "primary",
  type = "button",
  icon,
  iconEnd,
  loading = false,
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
        {iconEnd && <Icon name={iconEnd} />}
      </span>
      <span className="ui-button__label ui-button__label--loading" aria-hidden={!loading || undefined}>
        <Icon name="loader" className={loading ? "ui-spin" : undefined} />
        {loadingLabel}
      </span>
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
