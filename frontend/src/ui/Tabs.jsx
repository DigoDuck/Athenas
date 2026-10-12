import { useId, useRef } from "react";

// Text tabs with a bronze underline. Arrow keys, Home and End move between tabs.
// items: [{ id, label, content }]
export default function Tabs({ label, items, value, onChange }) {
  const baseId = useId();
  const refs = useRef({});
  const current = items.find((item) => item.id === value) ?? items[0];

  function focusAt(index) {
    const item = items[(index + items.length) % items.length];
    onChange(item.id);
    refs.current[item.id]?.focus();
  }

  function onKeyDown(event) {
    const index = items.findIndex((item) => item.id === current.id);
    const moves = { ArrowRight: index + 1, ArrowLeft: index - 1, Home: 0, End: items.length - 1 };
    if (event.key in moves) {
      event.preventDefault();
      focusAt(moves[event.key]);
    }
  }

  return (
    <div className="ui-tabs">
      <div className="ui-tabs__list" role="tablist" aria-label={label} onKeyDown={onKeyDown}>
        {items.map((item) => {
          const selected = item.id === current.id;
          return (
            <button
              key={item.id}
              ref={(node) => {
                refs.current[item.id] = node;
              }}
              type="button"
              role="tab"
              id={`${baseId}-tab-${item.id}`}
              aria-selected={selected}
              aria-controls={`${baseId}-panel-${item.id}`}
              tabIndex={selected ? 0 : -1}
              className="ui-tabs__tab"
              onClick={() => onChange(item.id)}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      <div
        className="ui-tabs__panel"
        role="tabpanel"
        id={`${baseId}-panel-${current.id}`}
        aria-labelledby={`${baseId}-tab-${current.id}`}
        tabIndex={0}
      >
        {current.content}
      </div>
    </div>
  );
}
