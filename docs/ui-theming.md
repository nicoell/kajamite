# Configure the change UI

Kajamite ships a ready-built React and shadcn interface. Adopters configure its
theme without rebuilding Kajamite or installing Node. The UI makes no CDN,
font-service, or theme-service requests.

## Standalone server

Save a theme beside the existing backend configuration. Add this table:

```toml
[ui]
theme = "theme.css"
```

The path is relative to the configuration file. Absolute paths also work.
Restart the Kajamite server and reconnect the client to load the new theme.
An already-open result can retain its previous resource. Theme-file watching
and live updates to existing results are not provided.

A minimal CSS theme contains light and dark variable blocks:

```css
:root {
  --primary: oklch(0.45 0.16 255);
  --primary-foreground: oklch(0.99 0 0);
  --radius: 0.75rem;
}
.dark {
  --primary: oklch(0.78 0.10 255);
  --primary-foreground: oklch(0.18 0.02 255);
}
```

Use a full palette to change card surfaces and text. `primary` affects controls
that use that token; it does not recolor every element. The default review button
uses the primary variant and follows `primary` and `primary-foreground`.

The default palette uses yellow-green accents with neutral light/dark cards.
The document background is transparent; the card remains opaque. See the
[presentation design](ui-design.md) for the information hierarchy and palette source.

## Export from tweakcn

Design a theme in [tweakcn](https://tweakcn.com). Save its `:root` and `.dark`
CSS variable blocks as `theme.css`, or save its shadcn registry JSON as
`theme.json`. Point `[ui].theme` to that local file.

The CSS importer accepts variable declarations in `:root` and `.dark`.
It ignores an optional `@theme inline` block because the packaged UI owns
Tailwind's utility mappings. Remove imports, `@font-face`, and other CSS rules.
The importer never executes a supplied stylesheet.

For registry JSON, Kajamite reads `cssVars.theme`, `cssVars.light`, and
`cssVars.dark`. It does not install registry dependencies or execute `files`
or `css` entries. It also accepts plain JSON with `theme`, `light`, and `dark`
token maps. `theme` contains shared values. Token names can omit the leading `--`.

Supported tokens include the standard shadcn surface/foreground pairs, primary,
secondary, muted, accent, destructive, border, input, ring, radius, font families,
spacing, tracking, shadow values, and chart/sidebar colors. Unused tokens have
no visual effect until a component uses them. Unknown tokens and unsafe values
fail configuration validation. Values unsupported by the browser fall back to
the existing palette. Themes are limited to 32 KiB and values to 512 characters.

Font-family settings select fonts already available on the device. They do not
download a font. Include system fallbacks, and check theme contrast in both modes.

## Embedding applications

An application that composes Kajamite's MCP server can supply the same tokens:

```python
from kajamite.server import create_server
from kajamite.theme import load_theme

server = create_server(engine, ui_theme=load_theme("theme.json"))
```

Or pass a Python mapping directly:

```python
server = create_server(engine, ui_theme={
    "theme": {"radius": "0.75rem"},
    "light": {"primary": "#2456a6"},
    "dark": {"primary": "#a8c7fa"},
})
```

Theme data configures the UI resource. It does not enter knowledge content,
mutation receipts, or tool arguments. Resource URIs include a theme fingerprint
so a different configured theme has a different cache key. Register each theme
in its own server instance when applications need separate configurations.

## Host appearance and precedence

The host selects light or dark mode through MCP Apps host-context messages.
Without a host preference, the UI follows the browser's system preference.
Open cards respond to host appearance changes without a rebuild.

The effective palette applies these layers in order:

1. Packaged neutral light/dark defaults.
2. Supported host style variables, mapped to shadcn tokens.
3. Explicit adopter tokens, with dark values overriding shared/light values.

Omit `[ui].theme` to follow the host and packaged defaults. Host palette changes
replace prior host overrides; removed values do not linger. Theme controls
change appearance inside the card, not the surrounding ChatGPT or Codex shell.

## Development

Frontend contributors use the [UI build instructions](../web/README.md).
Consumers use the configuration above. This separation is what “configurable
without rebuilding” means; it does not promise instant theme-file reload.
