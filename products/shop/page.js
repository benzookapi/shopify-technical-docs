const japanese = document.documentElement.lang === "ja";
const fontFamily = japanese
  ? "Noto Sans JP, ui-sans-serif, system-ui, sans-serif"
  : "Inter Tight, ui-sans-serif, system-ui, sans-serif";
const dialog = document.querySelector(".diagram-dialog");
const expanded = dialog.querySelector(".dialog-diagram");

document.querySelector(".diagram-close").addEventListener("click", () => dialog.close());
dialog.addEventListener("close", () => expanded.replaceChildren());

async function renderDiagrams() {
  try {
    const { default: mermaid } = await import("https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs");
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "base",
      fontFamily,
      flowchart: { useMaxWidth: false, htmlLabels: false, nodeSpacing: 24, rankSpacing: 34 },
      sequence: {
        useMaxWidth: false,
        actorFontSize: 12,
        messageFontSize: 12,
        noteFontSize: 12,
        mirrorActors: false,
        wrap: true,
        width: 135,
        actorMargin: 15,
        diagramMarginX: 10,
      },
      themeVariables: {
        primaryColor: "#e2f3eb",
        primaryTextColor: "#17221b",
        primaryBorderColor: "#008060",
        secondaryColor: "#e7f0f8",
        tertiaryColor: "#ffffff",
        lineColor: "#596660",
        fontSize: "12px",
        fontFamily,
      },
    });
    // Load the page font before Mermaid measures text, including Japanese labels.
    await document.fonts.ready;
    await mermaid.run({ querySelector: ".mermaid" });
    document.querySelectorAll(".diagram-wrap").forEach((figure) => {
      const svg = figure.querySelector("svg");
      if (!svg) return;
      const width = Math.ceil(svg.viewBox.baseVal.width);
      svg.style.width = `${width}px`;
      if (japanese) {
        // Mermaid may hyphenate CJK loop captions even with explicit line breaks.
        // Remove only the inserted ASCII hyphen after a Japanese character.
        const textNodes = document.createTreeWalker(svg, NodeFilter.SHOW_TEXT);
        while (textNodes.nextNode()) {
          const node = textNodes.currentNode;
          node.nodeValue = node.nodeValue.replace(/([\u3040-\u30ff\u3400-\u9fff])-(?=$|\s)/g, "$1");
        }
        const controls = { alt: "条件", loop: "繰り返し", opt: "任意" };
        svg.querySelectorAll(".labelText").forEach((label) => {
          const translated = controls[label.textContent.trim()];
          if (translated) label.textContent = translated;
        });
      }
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", figure.getAttribute("aria-label"));
      const button = figure.querySelector(".diagram-expand");
      button.hidden = false;
      button.addEventListener("click", () => {
        expanded.replaceChildren(svg.cloneNode(true));
        dialog.showModal();
      });
    });
    document.documentElement.dataset.diagrams = "ready";
  } catch (error) {
    document.getElementById("diagram-status").textContent = document.body.dataset.diagramError;
    document.documentElement.dataset.diagrams = "error";
    console.error("Shop diagram rendering failed", error);
  }
}

const tocLinks = document.querySelectorAll(".contents a");
const observer = new IntersectionObserver((entries) => {
  const visible = entries.find((entry) => entry.isIntersecting);
  if (!visible) return;
  tocLinks.forEach((link) => {
    if (link.hash === `#${visible.target.id}`) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
}, { rootMargin: "-5% 0px -75% 0px" });
document.querySelectorAll("main .section").forEach((section) => observer.observe(section));

renderDiagrams();
