// The request the "Novo tema" screen copies for any chat AI (DECISIONS.md D-040). It carries the
// content contract of spec 4.1 and the athenas-tema skill's rules, so a chat answer passes the
// same parser as a pushed theme. The ## headings are the parser's contract: never reword them.

export const LEVELS = [
  ["iniciante", "Iniciante"],
  ["intermediário", "Intermediário"],
  ["avançado", "Avançado"],
  ["especialista", "Especialista"],
];

const HEADINGS = [
  "Objetivo",
  "Pré-requisitos",
  "Ideia central",
  "Explicação",
  "Exemplo",
  "Confusões comuns",
  "Prática",
  "Resumo para o caderno",
  "Fontes",
  "Flashcards",
];

export function buildRequest({ theme, goal, area, level, origin, concepts }) {
  const done = concepts.length
    ? concepts.map((name, i) => `${i + 1}. ${name}`).join("\n")
    : "Nenhum. Este é o primeiro.";
  return `Você vai preparar material de estudo para o Athenas, meu app pessoal de estudos. Um leitor automático lê a sua resposta, então siga o formato à risca.

Tema: ${theme}
Objetivo: ${goal || "uma base prática, a partir do zero"}
Área: ${area}
Nível: ${level}

Conceitos que a trilha já tem, em ordem de estudo:
${done}

# O que fazer

Escreva só o próximo conceito da trilha, na ordem de estudo. A trilha inteira deve ter de 3 a 5 conceitos. Se os conceitos acima já cobrem o tema, responda apenas TRILHA COMPLETA.

Divida o conceito em 2 a 4 subtemas, cada um para uma sessão de 20 a 40 minutos, e escreva um documento por subtema. Dê nomes curtos, em português, e diferentes dos conceitos acima.

# Formato da resposta

Responda com um único bloco de código que abre com a linha ~~~~markdown e fecha com a linha ~~~~, sem nada antes nem depois dele. Dentro do bloco, os documentos um depois do outro. Cada documento começa com este cabeçalho, trocando só o que está entre < e >:

---
area: ${area}
conceito: <nome do conceito>
subtema: <nome do subtema>
nivel: ${level}
origem: ${origin}
---

Depois do cabeçalho vêm estes dez títulos, nesta ordem, escritos exatamente assim, e nenhum outro título com ##:

${HEADINGS.map((h) => `## ${h}`).join("\n")}

O que vai em cada título:
- Objetivo: uma frase com o que vou conseguir fazer depois do subtema.
- Pré-requisitos: o que preciso saber antes, em uma ou duas linhas.
- Ideia central: duas a quatro frases que se sustentam sozinhas.
- Explicação: de 300 a 700 palavras, com as suas palavras.
- Exemplo: concreto. Código para programação; frases em contexto para inglês.
- Confusões comuns: de dois a quatro enganos, cada um com a correção.
- Prática: de duas a quatro perguntas, e ao menos uma pede para aplicar, não só lembrar. Cada pergunta no formato abaixo, com a resposta na linha seguinte:
### P1: <pergunta>
Resposta de referência: <resposta>
- Resumo para o caderno: de quatro a oito linhas curtas, para eu copiar à mão.
- Fontes: um link por linha, no formato - https://...
- Flashcards: de três a seis cartões, um fato por cartão, uma linha cada, sem :: dentro do texto, no formato:
- C1: <frente> :: <verso>

# Fontes e confiança

Em Fontes, ponha só links de páginas que você abriu nesta conversa ou de documentação oficial que você tem certeza de que existe. Se houver fontes anexadas a esta conversa (como num caderno do Gemini Notebook), escreva a partir delas.

Toda afirmação que as suas fontes não sustentam vai num destaque assim, com o link quando houver:
> [!ia] <a afirmação>
> Fonte: <link>

Não inclua imagens. Escreva em português do Brasil; código, comandos e nomes técnicos ficam como são.`;
}

// Sent back to the AI when the check finds problems, so fixing one is a copy and a paste.
export function buildCorrection(report) {
  const lines = [
    ...report.errors,
    // A subtopic that keeps its own text is Diogo's to change, not the AI's.
    ...report.documents
      .filter((d) => d.action !== "keep" && d.action !== "same")
      .flatMap((d) =>
      [...d.errors, ...d.warnings].map((p) => `${d.subtema || "Documento sem subtema"}: ${p}`),
    ),
  ];
  return `O leitor do Athenas encontrou estes problemas na sua resposta:

${lines.map((line) => `- ${line}`).join("\n")}

Corrija-os e mande de novo todos os documentos, completos, no mesmo formato: um único bloco de código que abre com ~~~~markdown e fecha com ~~~~.`;
}
