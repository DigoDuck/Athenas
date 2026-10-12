import Icon from "./Icon.jsx";

// Empty, error and success states: icon, title, explanation and one action.
// Errors say what happened and how to recover; never claim a save before it is confirmed.
const kinds = {
  empty: { icon: "file-text", role: undefined },
  error: { icon: "alert-circle", role: "alert" },
  success: { icon: "check-circle", role: "status" },
};

export default function StateMessage({ kind = "empty", title, children, action }) {
  const { icon, role } = kinds[kind];
  return (
    <div className={`ui-state ui-state--${kind}`} role={role}>
      <Icon name={icon} size={40} />
      <p className="ui-state__title">{title}</p>
      {children && <p className="ui-state__text">{children}</p>}
      {action && <div className="ui-state__action">{action}</div>}
    </div>
  );
}
