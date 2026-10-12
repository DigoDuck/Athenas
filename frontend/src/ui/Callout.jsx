import Icon from "./Icon.jsx";

// notebook: "Para o caderno". ai: a `> [!ia]` complement from the content; without
// a source it is marked "complemento sem fonte" (spec 4.2, C4). info: complementary note.
const variants = {
  notebook: { icon: "file-text", title: "Para o caderno" },
  ai: { icon: "info", title: "Complemento da IA" },
  info: { icon: "info", title: null },
};

export default function Callout({ variant = "notebook", title, source, children }) {
  const preset = variants[variant];
  const heading = title ?? preset.title;
  const unsourced = variant === "ai" && !source;
  return (
    <aside className={`ui-callout ui-callout--${variant}`}>
      <Icon name={preset.icon} size={24} />
      <div className="ui-callout__body">
        {heading && <p className="ui-callout__title">{heading}</p>}
        {unsourced && <p className="ui-callout__flag">Complemento sem fonte</p>}
        <div className="ui-callout__content">{children}</div>
        {source && <p className="t-meta">Fonte: {source}</p>}
      </div>
    </aside>
  );
}
