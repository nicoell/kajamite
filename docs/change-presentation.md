# Change presentation

The inline receipt shows an outcome, a note address, and change counts.
Values remain hidden until the reader selects **View changes**.
A change means a changed passage, metadata field, or location.
The note count remains separate from that count.
Equal values do not count as changed passages.

The component requests fullscreen through `ui/request-display-mode` only when the host advertises that mode.
Host refusal, timeout, or missing support leaves the same details available inline.
The first disclosure shows three changes. **Show more** reveals three more.
Technical evidence is a separate disclosure.
Closing the host view restores the compact summary.
The view reports its intrinsic height and uses host theme variables.
Source text remains inert text, including note paths and HTML-like content.

Mutation tools share this view, including record maintenance.
Maintenance counts new changed notes separately from replayed operations and errors.
Preview, unchanged content, replay, cancellation, and missing receipts have distinct states.
An error never implies that a pending write was rolled back.
The complete structured receipt and labeled text remain available without UI.
The agent summarizes the outcome in chat and supplies detail on request.

The component has no conversation-wide event store.
It cannot count unrelated filesystem edits or actions from other providers.
A compatible host decides where fullscreen appears. No custom sidebar API is assumed.
Browser acceptance simulates host messages. It does not prove availability in a particular user account or client.

## Sources

- [OpenAI UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines): compact inline results, disclosure, and expanded views.
- [OpenAI UI integration](https://developers.openai.com/plugins/build/chatgpt-ui): MCP Apps first, with useful non-UI results.
- [MCP Apps specification](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx): display-mode negotiation, host context, and resize notifications.

## Browser acceptance

Set `KAJAMITE_BROWSER` to an existing Chromium or Chromium headless-shell executable.
Run `PYTHONPATH=src python -m unittest discover -s tests -p test_ui.py -v`.
The test uses synthetic notes and a temporary host page.
It does not install a browser or change the configured knowledge base.
