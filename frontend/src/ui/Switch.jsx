import { useId } from "react";

// On/off setting, such as focus mode. The state is also written as text.
export default function Switch({ label, description, checked, onChange }) {
  const id = useId();
  return (
    <div className="ui-switch">
      <button
        type="button"
        role="switch"
        id={id}
        aria-checked={checked}
        aria-describedby={description ? `${id}-desc` : undefined}
        className="ui-switch__control"
        onClick={() => onChange(!checked)}
      >
        <span className="ui-switch__thumb" />
      </button>
      <div>
        <label className="ui-switch__label" htmlFor={id}>
          {label} <span className="ui-switch__state">({checked ? "ligado" : "desligado"})</span>
        </label>
        {description && (
          <p className="t-meta" id={`${id}-desc`}>
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
