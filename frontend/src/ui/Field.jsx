import { useId } from "react";

import Icon from "./Icon.jsx";

// Label always above the control; the placeholder never replaces it.
// `error` turns the border red and adds an icon and a message, so state never depends on color.
function useFieldIds(error, help, status) {
  const id = useId();
  const helpId = help ? `${id}-help` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const statusId = status ? `${id}-status` : undefined;
  const describedBy = [errorId, helpId, statusId].filter(Boolean).join(" ") || undefined;
  return { id, helpId, errorId, statusId, describedBy };
}

function FieldShell({ ids, label, required, help, error, status, children }) {
  return (
    <div className="ui-field" data-invalid={error ? "true" : undefined}>
      <label className="ui-field__label" htmlFor={ids.id}>
        {label}
        {required && <span className="ui-field__required"> (obrigatório)</span>}
      </label>
      {children}
      {error && (
        <p className="ui-field__error" id={ids.errorId}>
          <Icon name="alert-circle" />
          {error}
        </p>
      )}
      {help && (
        <p className="ui-field__help" id={ids.helpId}>
          {help}
        </p>
      )}
      {status && (
        <p className="ui-field__status" id={ids.statusId} role="status">
          {status}
        </p>
      )}
    </div>
  );
}

export function TextField({ label, help, error, required, className = "", ...rest }) {
  const ids = useFieldIds(error, help);
  return (
    <FieldShell ids={ids} label={label} required={required} help={help} error={error}>
      <input
        id={ids.id}
        className={`ui-input ${className}`.trim()}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        {...rest}
      />
    </FieldShell>
  );
}

// Long answers. `status` shows the draft state, such as "Rascunho salvo às 14:32".
export function TextArea({ label, help, error, status, required, rows = 6, className = "", ...rest }) {
  const ids = useFieldIds(error, help, status);
  return (
    <FieldShell ids={ids} label={label} required={required} help={help} error={error} status={status}>
      <textarea
        id={ids.id}
        rows={rows}
        className={`ui-input ui-input--area ${className}`.trim()}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        {...rest}
      />
    </FieldShell>
  );
}
