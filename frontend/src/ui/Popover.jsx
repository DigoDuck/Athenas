import { useEffect, useId, useRef, useState } from "react";

// A button that opens a small panel under it: the block list on the reading screen, a step's
// actions on the Roadmap. Escape or a click outside closes it; Escape returns focus to the button.
// `children` is a function that receives `close`, so an action inside can close the panel.
// `label` names the button when `trigger` is only an icon. `align="end"` opens it to the left.
export default function Popover({ trigger, label, align = "start", className = "", children }) {
  const [open, setOpen] = useState(false);
  const root = useRef(null);
  const id = useId();
  // By id, not by ref: `close` is handed to children during render.
  const focusTrigger = () => document.getElementById(`${id}-trigger`)?.focus();

  useEffect(() => {
    if (!open) return;
    // The current item when there is one, so the list opens where the reader is.
    const panel = root.current.querySelector(".ui-popover__panel");
    (panel.querySelector("[aria-current]") ?? panel.querySelector("button, a, select, input"))?.focus();
    function onPointerDown(e) {
      if (!root.current.contains(e.target)) setOpen(false);
    }
    function onKeyDown(e) {
      if (e.key !== "Escape") return;
      setOpen(false);
      document.getElementById(`${id}-trigger`)?.focus();
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, id]);

  function close() {
    setOpen(false);
    focusTrigger();
  }

  return (
    <div className={`ui-popover ${className}`.trim()} ref={root}>
      <button
        id={`${id}-trigger`}
        type="button"
        className="ui-popover__trigger"
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        aria-label={label}
        onClick={() => setOpen(!open)}
      >
        {trigger}
      </button>
      {open && (
        <div id={id} className="ui-popover__panel" data-align={align}>
          {children(close)}
        </div>
      )}
    </div>
  );
}
