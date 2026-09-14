# Change result presentation

The card helps a reader answer three questions: what happened, which notes were
involved, and what changed. It reports stored knowledge changes, not external
business events. A saved status field does not prove a reservation or approval.

## Information priority

| Information | Presentation | Reason |
| --- | --- | --- |
| Outcome and affected scope | Always visible | Distinguish saved changes, previews, replay, cancellation, and uncertainty. |
| Note name and path | Always visible for one note | Identify the object without requiring knowledge of the receipt schema. |
| Actual changed text or labeled fields | First two changes visible; three items for batches | A count alone cannot explain the result. |
| Failed item and error | Visible before disclosure | A failure must not be hidden behind a successful count. |
| Remaining edits | Explicit remaining count and details action | Keep large operations bounded without implying a complete summary. |
| Exact comparison | Stacked before/after text with changed spans emphasized | Preserve reading order at narrow widths and avoid large empty columns. |
| Long excerpts | First 600 characters with local disclosure | Large values must not dominate every review. Receipt truncation stays explicit. |
| Verification, operation coverage | About this result, inside details | Useful for investigation, not routine reading. |
| Raw receipt and record revision counter | Raw receipt, inside About this result | These values explain implementation state, not the substance of an edit. |

Unknown field names are converted from snake case to labels. Their values remain
verbatim. The renderer does not invent domain descriptions. Batch details keep
note paths beside each group. Internal record counters do not inflate the visible
change count. They remain available in the original receipt.

Added and removed notes show one content excerpt. Field edits show a labeled
transition. Text edits preserve the original text and emphasize a common-prefix /
common-suffix difference at word boundaries. This is a bounded comparison, not a
full multi-hunk diff or an AI-generated summary. Unchanged context remains present.
Source strings never execute as HTML. No additional retrieval is performed.

## Appearance and embedding

The default palette derives from the public Shopify theme export at
https://tweakcn.com/r/themes/cmr2oqrzb000104ky3d4o23e0. Primary and accent tokens
shift toward yellow-green, with light primary `oklch(0.78 0.18 119)` and dark primary
`oklch(0.84 0.18 119)`. Neutral surfaces, radius, and typography structure remain.
System font stacks avoid font downloads. Exported theme styles are represented as
static tokens, not a runtime dependency on the theme service.

Both the document root and body are transparent. The card uses its opaque card
token. The host controls the surface behind the iframe; it may still apply its own
wrapper background. Default tokens, host appearance, and explicit adopter tokens
retain their existing precedence. The default palette uses the same semantic
colors as configured themes, including comparison highlights.

## Basis and acceptance limits

The hierarchy applies progressive disclosure to secondary information while
keeping primary facts and errors visible. See
https://www.nngroup.com/articles/progressive-disclosure/ and the official shadcn
composition guidance at https://ui.shadcn.com/docs/components/radix/collapsible.
The retained Card, Button, and Collapsible primitives provide semantic controls,
focus behavior, and controlled disclosure. No new component library is required.

Browser acceptance covers visible summaries, field labels, hidden diagnostics,
light/dark and adopter tokens, transparent embedding, narrow widths, inert text,
pagination, and host expansion fallback. Synthetic previews test the actual bundle.
They do not establish user usability success or actual ChatGPT host presentation;
those require review in the target host.
