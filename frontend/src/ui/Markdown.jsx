import { Fragment } from "react";

// The Markdown subset study content uses (spec 4.1), rendered as React elements: no HTML from
// the text reaches the page, and links and images accept only http(s) or same-site paths.
// Covered: paragraphs, ### headings, lists, quotes, tables, rules, images with a caption, and
// inline bold, italic, code, links and bare URLs.
export default function Markdown({ text }) {
  return <div className="ui-markdown">{blocks(text)}</div>;
}

// Every URL found in a text, as written in a link or bare, in order and without repeats.
export function markdownLinks(text) {
  const links = new Map();
  for (const m of text.matchAll(/\[([^\]]+)\]\((\S+?)\)|<?(https?:\/\/[^\s<>)]+)>?/g)) {
    const url = trimUrl(m[2] ?? m[3]);
    if (safeUrl(url) && !links.has(url)) links.set(url, m[1] ?? null);
  }
  return [...links].map(([url, label]) => ({ url, label }));
}

const LIST_ITEM = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/;
const IMAGE_LINE = /^!\[([^\]]*)\]\((\S+?)(?:\s+"([^"]*)")?\)$/;
const TABLE_RULE = /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$/;

function blocks(text) {
  const lines = text.replace(/\r\n?/g, "\n").split("\n");
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    const key = out.length;
    if (!trimmed) {
      i += 1;
    } else if (/^#{1,6}\s/.test(trimmed)) {
      // The block's own heading is the h2, so headings inside it start at h3.
      const level = Math.min(Math.max(trimmed.match(/^#+/)[0].length, 3), 6);
      const Tag = `h${level}`;
      out.push(<Tag key={key}>{inline(trimmed.replace(/^#+\s+/, ""))}</Tag>);
      i += 1;
    } else if (/^([-*_])(\s*\1){2,}$/.test(trimmed)) {
      out.push(<hr key={key} />);
      i += 1;
    } else if (IMAGE_LINE.test(trimmed)) {
      const [, alt, src, title] = trimmed.match(IMAGE_LINE);
      out.push(<Figure key={key} alt={alt} src={src} caption={title || alt} />);
      i += 1;
    } else if (trimmed.startsWith(">")) {
      const quoted = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quoted.push(lines[i].trim().replace(/^>\s?/, ""));
        i += 1;
      }
      out.push(<blockquote key={key}>{blocks(quoted.join("\n"))}</blockquote>);
    } else if (trimmed.startsWith("|") && TABLE_RULE.test(lines[i + 1]?.trim() ?? "")) {
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        rows.push(lines[i].trim());
        i += 1;
      }
      out.push(<Table key={key} rows={rows} />);
    } else if (LIST_ITEM.test(line)) {
      const indent = line.match(LIST_ITEM)[1].length;
      const ordered = /\d/.test(line.match(LIST_ITEM)[2]);
      const items = [];
      while (i < lines.length) {
        const item = lines[i].match(LIST_ITEM);
        if (item && item[1].length <= indent) {
          if (/\d/.test(item[2]) !== ordered) break;
          items.push([item[3]]);
          i += 1;
        } else if (items.length && lines[i].trim() && /^\s/.test(lines[i])) {
          // An indented line continues the item, nested lists included.
          items.at(-1).push(lines[i].slice(Math.min(indent + 2, lines[i].search(/\S/))));
          i += 1;
        } else {
          break;
        }
      }
      const List = ordered ? "ol" : "ul";
      const start = ordered ? parseInt(line.trim(), 10) : undefined;
      out.push(
        <List key={key} start={start !== 1 ? start : undefined}>
          {items.map((item, n) => (
            <li key={n}>{item.length === 1 ? inline(item[0]) : blocks(item.join("\n"))}</li>
          ))}
        </List>,
      );
    } else {
      const paragraph = [];
      while (i < lines.length && lines[i].trim() && !startsBlock(lines, i)) {
        paragraph.push(lines[i]);
        i += 1;
      }
      // Lines wrapped in the source make one flowing paragraph, as in CommonMark; a line that
      // ends in two spaces or a backslash keeps its break (DECISIONS.md D-034).
      out.push(
        <p key={key}>
          {paragraph.map((part, n) => (
            <Fragment key={n}>
              {n > 0 && (/( {2}|\\)$/.test(paragraph[n - 1]) ? <br /> : " ")}
              {inline(part.trim().replace(/\\$/, ""))}
            </Fragment>
          ))}
        </p>,
      );
    }
  }
  return out;
}

function startsBlock(lines, i) {
  const trimmed = lines[i].trim();
  return (
    /^#{1,6}\s/.test(trimmed) ||
    /^([-*_])(\s*\1){2,}$/.test(trimmed) ||
    trimmed.startsWith(">") ||
    IMAGE_LINE.test(trimmed) ||
    LIST_ITEM.test(lines[i]) ||
    (trimmed.startsWith("|") && TABLE_RULE.test(lines[i + 1]?.trim() ?? ""))
  );
}

function Figure({ alt, src, caption }) {
  if (!safeUrl(src)) return <p>{alt}</p>;
  return (
    <figure>
      <img src={src} alt={alt} loading="lazy" />
      {caption && <figcaption>{caption}</figcaption>}
    </figure>
  );
}

function Table({ rows }) {
  const cells = (row) =>
    row
      .replace(/^\||\|$/g, "")
      .split("|")
      .map((cell) => cell.trim());
  const [head, , ...body] = rows;
  return (
    <div className="ui-markdown__table">
      <table>
        <thead>
          <tr>
            {cells(head).map((cell, n) => (
              <th key={n}>{inline(cell)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, r) => (
            <tr key={r}>
              {cells(row).map((cell, n) => (
                <td key={n}>{inline(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// One alternation, tried left to right; the first group that matched names the token.
const INLINE = new RegExp(
  [
    /`([^`]+)`/.source,
    /!\[([^\]]*)\]\((\S+?)\)/.source,
    /\[([^\]]+)\]\((\S+?)(?:\s+"[^"]*")?\)/.source,
    /<(https?:\/\/[^\s>]+)>/.source,
    /(https?:\/\/[^\s<>)\]]+)/.source,
    /\*\*(.+?)\*\*|__(.+?)__/.source,
    /\*([^*\s](?:[^*]*?[^*\s])?)\*/.source,
    // `snake_case` is not italic: the underscores must sit outside a word.
    /(?<![\p{L}\p{N}_])_([^_\s](?:[^_]*?[^_\s])?)_(?![\p{L}\p{N}_])/.source,
  ].join("|"),
  "gu",
);

function inline(text) {
  const out = [];
  let last = 0;
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const key = m.index;
    const [, code, alt, src, label, href, auto, bare, bold, bold2, italic, italic2] = m;
    if (code !== undefined) {
      out.push(<code key={key}>{code}</code>);
    } else if (src !== undefined) {
      out.push(safeUrl(src) ? <img key={key} src={src} alt={alt} /> : alt);
    } else if (href !== undefined) {
      out.push(<Link key={key} href={href}>{inline(label)}</Link>);
    } else if (auto !== undefined || bare !== undefined) {
      const url = trimUrl(auto ?? bare);
      out.push(<Link key={key} href={url}>{url}</Link>);
      // A sentence's final period is not part of the URL.
      if (bare !== undefined && url.length < bare.length) out.push(bare.slice(url.length));
    } else if (bold !== undefined || bold2 !== undefined) {
      out.push(<strong key={key}>{inline(bold ?? bold2)}</strong>);
    } else {
      out.push(<em key={key}>{inline(italic ?? italic2)}</em>);
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out.map((part, n) => (typeof part === "string" ? <Fragment key={`t${n}`}>{part}</Fragment> : part));
}

function Link({ href, children }) {
  if (!safeUrl(href)) return children;
  const external = /^https?:/i.test(href);
  return (
    <a href={href} {...(external && { target: "_blank", rel: "noreferrer" })}>
      {children}
    </a>
  );
}

function trimUrl(url) {
  return url.replace(/[.,;:!?]+$/, "");
}

export function safeUrl(url) {
  return /^https?:\/\//i.test(url) || /^\/(?!\/)/.test(url);
}
