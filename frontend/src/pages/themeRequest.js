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

export function buildRequest({ theme, goal, area, level, origin, concepts, taken }) {
  const done = concepts.length
    ? concepts.map((name, i) => `${i + 1}. ${name}`).join("\n")
    : "Nenhum. Este é o primeiro.";
  // Same name, same concept: the app files the subtopics under the one that exists (D-040).
  const others = taken.length
    ? `\n\nOutros conceitos que já existem na área ${area}, de outras trilhas: ${taken.join("; ")}. Não use esses nomes, a não ser que seja exatamente o mesmo conceito.`
    : "";
  return `Você vai preparar material de estudo para o Athenas, meu app pessoal de estudos. Um leitor automático lê a sua resposta, então siga o formato à risca.

Tema: ${theme}
Objetivo: ${goal || "uma base prática, a partir do zero"}
Área: ${area}
Nível: ${level}

Conceitos que a trilha já tem, em ordem de estudo:
${done}${others}

# O que fazer

Escreva só o próximo conceito da trilha, na ordem de estudo. A trilha inteira deve ter de 3 a 5 conceitos. Se os conceitos acima já cobrem o tema, responda apenas TRILHA COMPLETA.

Divida o conceito em 2 a 4 subtemas, cada um para uma sessão de 20 a 40 minutos, e escreva um documento por subtema. Dê nomes curtos, em português, e diferentes dos conceitos acima.

# Formato da resposta

Responda com um único bloco de código que abre com a linha ~~~~markdown e fecha com a linha ~~~~, sem nada antes nem depois dele. Dentro do bloco, os documentos um depois do outro e, depois do último, a linha <!-- fim -->, que mostra ao app que a resposta chegou inteira. Cada documento começa com este cabeçalho, substituindo cada <...> inteiro pelo nome real, sem os sinais < e >:

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
- Prática: de duas a quatro perguntas, e ao menos uma pede para aplicar, não só lembrar.
- Resumo para o caderno: de quatro a oito linhas curtas, para eu copiar à mão.
- Fontes: um link por linha.
- Flashcards: de três a seis cartões, um fato por cartão, uma linha cada, sem :: dentro do texto.

Em Prática, cada pergunta tem um número e cabe inteira na linha do ###, com a resposta na linha seguinte, assim:

### P1: Qual problema o encapsulamento resolve?
Resposta de referência: Impede que outro código mude o estado interno do objeto sem passar pelos métodos dele.

Se uma pergunta precisar de código, ponha o código no Exemplo e cite-o na pergunta: o app mostra só a linha do ###.

Em Flashcards, cada cartão começa com hífen e um número, com a frente e o verso separados por ::, assim:

- C1: O que o encapsulamento esconde? :: O estado interno do objeto.

Em Fontes, cada link começa com hífen, assim:

- https://docs.python.org/pt-br/3/tutorial/classes.html

Esses três exemplos mostram só o formato; escreva perguntas, cartões e links do tema.

# Fontes e confiança

Em Fontes, ponha só links de páginas que você abriu nesta conversa ou de documentação oficial que você tem certeza de que existe. Se houver fontes anexadas a esta conversa (como num caderno do Gemini Notebook), escreva a partir delas.

Toda afirmação que as suas fontes não sustentam vai num destaque assim, com o link quando houver:

> [!ia] A afirmação.
> Fonte: https://...

Não inclua imagens. Escreva em português do Brasil; código, comandos e nomes técnicos ficam como são.`;
}

// Sent back to the AI when the check finds problems, so fixing one is a copy and a paste.
// Null when there is nothing the AI could fix.
export function buildCorrection(report) {
  const lines = [
    // "TRILHA COMPLETA" is an answer, not a mistake; with no document at all, the fix is
    // usually how the answer was copied, which only Diogo can change.
    ...(report.complete || !report.documents.length ? [] : report.errors),
    // A subtopic that keeps its own text is Diogo's to change; only a broken split is the AI's.
    // Reusing a concept the request listed is right, so its note is not a problem either.
    // A cut is the AI's to fix even there: the document it was writing did not arrive.
    ...report.documents.flatMap((d) =>
      [
        ...d.errors,
        ...d.warnings.filter((p) => !["keep", "same"].includes(d.action) || p.includes("cortada")),
      ]
        .filter((p) => p !== d.joins_track)
        .map((p) => `${d.subtema || "Documento sem subtema"}: ${p}`),
    ),
  ];
  if (!lines.length) return null;
  return `O leitor do Athenas encontrou estes problemas na sua resposta:

${lines.map((line) => `- ${line}`).join("\n")}

Corrija-os e mande de novo todos os documentos, completos, no mesmo formato: um único bloco de código que abre com ~~~~markdown, termina com a linha <!-- fim --> e fecha com ~~~~.`;
}
