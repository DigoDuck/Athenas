// Self-check for src/ui/Markdown.jsx, the trust boundary for AI-written study text (D-031).
// Run with `npm run check:markdown`; it loads the component through Vite, so no test runner.
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const vite = await createServer({ server: { middlewareMode: true }, appType: "custom", logLevel: "error" });
try {
  const { default: Markdown, markdownLinks } = await vite.ssrLoadModule("/src/ui/Markdown.jsx");
  const html = (text) => renderToStaticMarkup(createElement(Markdown, { text }));

  // Formatting the content actually uses.
  assert.match(html("Um **termo** e *ênfase* com `code`."), /<strong>termo<\/strong>.*<em>ênfase<\/em>.*<code>code<\/code>/);
  assert.match(html("nome_completo e snake_case"), /^<div class="ui-markdown"><p>nome_completo e snake_case<\/p><\/div>$/);
  assert.match(html("1. um\n2. dois\n   - filho"), /<ol><li>um<\/li><li><p>dois<\/p><ul><li>filho<\/li><\/ul><\/li><\/ol>/);
  assert.match(html("| a | b |\n| --- | --- |\n| 1 | 2 |"), /<th>a<\/th>.*<td>2<\/td>/);
  assert.match(html('![Diagrama](/media/x.png "Legenda")'), /<img src="\/media\/x.png" alt="Diagrama".*<figcaption>Legenda<\/figcaption>/);
  assert.match(html("Veja https://a.org/x."), /<a href="https:\/\/a.org\/x" target="_blank" rel="noreferrer">https:\/\/a.org\/x<\/a>\./);

  // No HTML from the text reaches the page: it is escaped as text.
  const injected = html('<script>alert(1)</script> <img src=x onerror="alert(1)">');
  assert.doesNotMatch(injected, /<script|<img/);
  assert.match(injected, /&lt;script&gt;/);

  // Links and images take only http(s) or same-site paths.
  for (const url of ["javascript:alert(1)", "JaVaScRiPt:alert(1)", "data:text/html,x", "//evil.example/x", "vbscript:x"]) {
    const out = html(`[link](${url}) ![img](${url})\n\n![fig](${url})`);
    assert.doesNotMatch(out, /href=|src=/, `${url} must not become a link or image: ${out}`);
  }
  assert.deepEqual(
    markdownLinks("[A](https://a.org) javascript:x https://b.org/y. [C](data:x)").map((l) => l.url),
    ["https://a.org", "https://b.org/y"],
  );
  console.log("Markdown self-check passed");
} finally {
  await vite.close();
}
