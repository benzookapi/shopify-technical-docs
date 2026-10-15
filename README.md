# Shopify Technical Docs

This repository is a documentation library for detailed specifications and process flows across Shopify products.

The goal is to collect product-specific architecture notes, integration behavior, state transitions, and Mermaid-based flow diagrams in one place so they can be reused for technical discussions, partner enablement, and implementation planning.

## Documents

| Document | Shopify product | Coverage |
| --- | --- | --- |
| [Shopify Collective Architecture](./products/shopify-collective/architecture.md) | Shopify Collective | Retailer and supplier flows for product import, price and inventory sync, shipping, orders, automatic payments, fulfillment, cancellations, returns, and pricing-related changes. |
| [Shop Value, Channels, and Architecture](./products/shop/architecture.md) | Shop | Business value, Shop Pay in Checkout, Shop channel and Agentic Commerce, Shop Minis architecture, Shop Pay off Shopify payment and order flows, Shop.md, subscriptions, and multilingual FAQs. |

## GitHub Pages

The HTML site entry point is [`index.html`](./index.html). Product pages live in product-specific directories, and each HTML page links back to the Markdown source used to build the visualization.

Rendered entry points:

- [English site](./index.html)
- [Shopify Collective English HTML](./products/shopify-collective/index.html)
- [Shopify Collective Japanese HTML](./products/shopify-collective/ja/index.html)
- [Shopify Collective English PPTX](./products/shopify-collective/shopify-collective-architecture.pptx)
- [Shopify Collective Japanese PPTX](./products/shopify-collective/ja/shopify-collective-architecture-ja.pptx)
- [Shop English HTML](./products/shop/index.html)
- [Shop Japanese HTML](./products/shop/ja/index.html)

The GitHub Wiki also includes [Demo & Pages](../../wiki/Demo-&-Pages) (`wiki/Demo-&-Pages`), which collects demo videos and links to the rendered pages.

## Updating the Shop page

The English content source is [`products/shop/architecture.md`](./products/shop/architecture.md). Japanese translations are maintained in [`products/shop/ja/content.json`](./products/shop/ja/content.json), with one entry for every source block, including diagrams, notes, and FAQs. Keep the same source URLs in both inputs; the generator localizes Shopify Help Center URLs and the Shop and Checkout marketing links in Japanese HTML.

After editing the source and its translations, regenerate both HTML pages with Python 3 (no third-party dependencies):

```sh
python3 scripts/build-shop.py
```

The generator rejects missing or stale translations and mismatched headings, diagram line counts, or source links. The generated English HTML is the master visual output, and Japanese HTML uses the same sections and layout with localized text. Shared styling and diagram behavior live in `products/shop/page.css` and `products/shop/page.js`. Inspect both languages in a browser after regeneration, including Mermaid rendering, mobile layout, diagram expansion, and FAQ controls. Commit the source, translations, and regenerated HTML together.

Shop demo videos will be added to the Wiki when available. Wiki edits are maintained manually and separately from the repository source.

## Disclaimer

This repository is not official Shopify documentation. The maintainers do not accept responsibility for the accuracy, completeness, or consequences of using this content. Use it at your own discretion as supplemental material for understanding Shopify concepts and workflows. Content may change without notice.
