import Icon from "./Icon.jsx";

// Every badge carries text and an icon, never color alone.
// The spec keeps study status, the review flag and cards due as separate fields;
// they get separate badges and must never be merged into one indicator.

const studyStatus = {
  not_started: { label: "Não iniciado", icon: "circle", tone: "neutral" },
  in_progress: { label: "Em andamento", icon: "clock", tone: "accent" },
  completed: { label: "Concluído", icon: "check-circle", tone: "success" },
};

function Badge({ tone = "neutral", icon, children }) {
  return (
    <span className={`ui-badge ui-badge--${tone}`}>
      {icon && <Icon name={icon} size={16} />}
      {children}
    </span>
  );
}

export function StudyStatusBadge({ status }) {
  const { label, icon, tone } = studyStatus[status];
  return (
    <Badge tone={tone} icon={icon}>
      {label}
    </Badge>
  );
}

// Manual flag Diogo sets on a subtopic.
export function ReviewFlagBadge() {
  return (
    <Badge tone="info" icon="bookmark">
      Marcado para revisar
    </Badge>
  );
}

// Automatic: the subtopic has cards due today. Never a count of overdue cards.
export function CardsDueBadge() {
  return (
    <Badge tone="info" icon="hourglass">
      Cartões para hoje
    </Badge>
  );
}

// Text an AI wrote (frontmatter `origem`, DECISIONS.md D-032): reading well does not make it
// correct, so it stays marked wherever Diogo reads, approves or compares against it.
export function GeneratedByBadge({ by }) {
  return (
    <Badge tone="info" icon="info">
      Gerado por {by}
    </Badge>
  );
}

// Neutral metadata, such as level or perceived difficulty.
export function Tag({ children }) {
  return <Badge tone="neutral">{children}</Badge>;
}

export default Badge;
