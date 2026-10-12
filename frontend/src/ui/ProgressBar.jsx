// Bronze fill, plus visible text and count. `unit` names what is counted.
export default function ProgressBar({ value, max, unit = "etapas", label }) {
  const percent = max > 0 ? Math.round((value / max) * 100) : 0;
  const text = `${value} de ${max} ${unit}`;
  return (
    <div className="ui-progress">
      <div
        className="ui-progress__track"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={value}
        aria-valuetext={text}
      >
        <div className="ui-progress__fill" style={{ width: `${percent}%` }} />
      </div>
      <span className="ui-progress__text">{text}</span>
    </div>
  );
}
