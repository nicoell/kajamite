"""Adopter-owned theme tokens; never execute an imported stylesheet."""
from collections.abc import Mapping
import json
from pathlib import Path
import re

COLOR_TOKENS = set('background foreground card card-foreground popover popover-foreground primary primary-foreground secondary secondary-foreground muted muted-foreground accent accent-foreground destructive destructive-foreground border input ring sidebar sidebar-foreground sidebar-primary sidebar-primary-foreground sidebar-accent sidebar-accent-foreground sidebar-border sidebar-ring'.split()) | {f'chart-{i}' for i in range(1, 6)}
TOKENS = COLOR_TOKENS | set('radius font-sans font-serif font-mono shadow-2xs shadow-xs shadow-sm shadow shadow-md shadow-lg shadow-xl shadow-2xl shadow-color shadow-opacity shadow-blur shadow-spread shadow-offset-x shadow-offset-y tracking-normal tracking-tighter tracking-tight tracking-wide tracking-wider tracking-widest letter-spacing spacing'.split())
MAX_BYTES = 32768


def validate_theme(value: Mapping | None) -> dict:
    if value is None:
        return {"light": {}, "dark": {}}
    if not isinstance(value, Mapping) or set(value) - {"theme", "light", "dark"}:
        raise ValueError("UI theme must contain only theme, light, and dark token maps")
    common = value.get("theme", {})
    if not isinstance(common, Mapping):
        raise ValueError("UI theme common tokens must be a token map")
    # Validate common tokens even if a mode later overrides them.
    if common:
        common = validate_theme({"light": common})["light"]
    result = {}
    for mode in ("light", "dark"):
        tokens = value.get(mode, {})
        if not isinstance(tokens, Mapping):
            raise ValueError(f"UI theme {mode} must be a token map")
        result[mode] = {}
        for key, val in tokens.items():
            name = key.removeprefix('--') if isinstance(key, str) else ''
            if name not in TOKENS:
                raise ValueError("UI theme contains an unsupported token")
            if name in result[mode]:
                raise ValueError("UI theme contains a duplicate token")
            if not isinstance(val, str) or not val.strip() or len(val) > 512:
                raise ValueError("UI theme values must be nonempty strings of at most 512 characters")
            # Tokens are values, not declarations, selectors, URLs, or code. Reject
            # escapes too: they must not disguise a URL or stylesheet delimiter.
            if re.search(r'[;{}<>@\\\x00-\x1f]|/\*|\*/|(?:url|image|image-set|expression)\s*\(', val, re.I):
                raise ValueError("UI theme values cannot contain CSS rules, URLs, or escapes")
            if re.search(r'https?\s*:|javascript\s*:', val, re.I):
                raise ValueError("UI theme values cannot contain URLs")
            result[mode][name] = val.strip()
        if 'letter-spacing' in result[mode] and 'tracking-normal' not in result[mode]:
            result[mode]['tracking-normal'] = result[mode]['letter-spacing']
        if mode == "light":
            result[mode] = dict(common) | result[mode]
    if len(json.dumps(result).encode()) > MAX_BYTES:
        raise ValueError("UI theme exceeds 32 KiB")
    return result


def parse_theme_css(css: str) -> dict:
    """Read tweakcn/shadcn :root and .dark variable blocks, not general CSS.

    Tailwind's exported @theme inline mapping is ignored: the compiled UI owns
    its utility mappings. Imports and all other selectors are rejected.
    """
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    result = {"light": {}, "dark": {}}
    block = re.compile(r'\s*(:root|\.dark|@theme\s+inline)\s*\{([^{}]*)\}', re.S)
    position = 0
    while css[position:].strip():
        match = block.match(css, position)
        if not match:
            raise ValueError("UI theme CSS must contain only :root, .dark, and optional @theme inline blocks; remove imports and other rules")
        selector, body = match.groups()
        if not selector.startswith('@theme'):
            target = result['light' if selector == ':root' else 'dark']
            for declaration in body.split(';'):
                if not declaration.strip():
                    continue
                key, separator, val = declaration.partition(':')
                if not separator or not key.strip().startswith('--'):
                    raise ValueError("UI theme CSS must contain CSS variable declarations")
                key = key.strip()[2:]
                if key in target:
                    raise ValueError("UI theme contains a duplicate token")
                target[key] = val.strip()
        position = match.end()
    return validate_theme(result)


def load_theme(path: str | Path) -> dict:
    path = Path(path)
    with path.open('rb') as source:
        raw = source.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("UI theme exceeds 32 KiB")
    text = raw.decode('utf-8-sig')
    if path.suffix.lower() == '.css':
        return parse_theme_css(text)
    value = json.loads(text)
    # The public shadcn/tweakcn registry export wraps maps in cssVars. Do not
    # execute registry files, dependencies, CSS, or scripts.
    if isinstance(value, dict) and 'cssVars' in value:
        value = value['cssVars']
    return validate_theme(value)
