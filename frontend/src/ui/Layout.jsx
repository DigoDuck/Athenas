// Spacing primitives. `gap` is a step of the spacing scale (1 = 4px ... 8 = 64px).

export function Stack({ as: Tag = "div", gap = 4, className = "", style, children, ...rest }) {
  return (
    <Tag
      className={`ui-stack ${className}`.trim()}
      style={{ "--ui-gap": `var(--space-${gap})`, ...style }}
      {...rest}
    >
      {children}
    </Tag>
  );
}

// Items side by side that wrap when there is no room, such as a field and its button.
// align: "start" | "center" | "end" (vertical); justify: "start" | "between" | "end".
export function Inline({
  as: Tag = "div",
  gap = 3,
  align = "center",
  justify = "start",
  className = "",
  style,
  children,
  ...rest
}) {
  return (
    <Tag
      className={`ui-inline ${className}`.trim()}
      data-align={align}
      data-justify={justify}
      style={{ "--ui-gap": `var(--space-${gap})`, ...style }}
      {...rest}
    >
      {children}
    </Tag>
  );
}
