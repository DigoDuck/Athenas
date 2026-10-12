// Opaque white surface for a self-contained task or piece of content.
export default function Panel({ as: Tag = "section", raised = false, className = "", children, ...rest }) {
  const classes = `ui-panel${raised ? " ui-panel--raised" : ""} ${className}`.trim();
  return (
    <Tag className={classes} {...rest}>
      {children}
    </Tag>
  );
}
