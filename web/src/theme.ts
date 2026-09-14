export type Theme = {
  light?: Record<string, string>;
  dark?: Record<string, string>;
};
export type HostContext = {
  theme?: string;
  displayMode?: string;
  availableDisplayModes?: string[];
  styles?: { variables?: Record<string, string> };
};
const colors =
  "background foreground card card-foreground popover popover-foreground primary primary-foreground secondary secondary-foreground muted muted-foreground accent accent-foreground destructive destructive-foreground border input ring sidebar sidebar-foreground sidebar-primary sidebar-primary-foreground sidebar-accent sidebar-accent-foreground sidebar-border sidebar-ring chart-1 chart-2 chart-3 chart-4 chart-5".split(
    " ",
  );
const fonts = ["font-sans", "font-serif", "font-mono"];
const shadows = [
  "shadow-2xs",
  "shadow-xs",
  "shadow-sm",
  "shadow",
  "shadow-md",
  "shadow-lg",
  "shadow-xl",
  "shadow-2xl",
];
const aliases: Record<string, string[]> = {
  "color-background-primary": ["background", "card", "popover"],
  "color-text-primary": ["foreground", "card-foreground", "popover-foreground"],
  "color-background-secondary": ["muted", "secondary"],
  "color-text-secondary": ["muted-foreground"],
  "color-border-primary": ["border"],
  "color-border-secondary": ["input"],
  "color-background-info": ["accent"],
  "color-text-info": ["accent-foreground"],
  "font-sans": ["font-sans"],
};
let applied = new Set<string>();
const element = document.documentElement;
const safe = (name: string, value: unknown): value is string => {
  if (
    typeof value !== "string" ||
    !value.trim() ||
    value.length > 512 ||
    /[;{}<>@\\\x00-\x1f]|\/\*|\*\/|(?:url|image|image-set|expression)\s*\(|https?\s*:|javascript\s*:/i.test(
      value,
    )
  )
    return false;
  const property =
    colors.includes(name) || name === "shadow-color"
      ? "color"
      : fonts.includes(name)
        ? "font-family"
        : shadows.includes(name)
          ? "box-shadow"
          : name.startsWith("tracking-") || name === "letter-spacing"
            ? "letter-spacing"
            : name === "radius"
              ? "border-radius"
              : null;
  if (property) return CSS.supports(property, value);
  return [
    "spacing",
    "shadow-blur",
    "shadow-spread",
    "shadow-offset-x",
    "shadow-offset-y",
  ].includes(name)
    ? CSS.supports("width", value)
    : name === "shadow-opacity" && /^0(?:\.\d+)?$|^1(?:\.0+)?$/.test(value);
};
export function applyTheme(theme: Theme, host: HostContext) {
  const dark =
    host.theme === "dark" ||
    (host.theme !== "light" &&
      matchMedia("(prefers-color-scheme: dark)").matches);
  element.classList.toggle("dark", dark);
  element.style.colorScheme = dark ? "dark" : "light";
  const values: Record<string, string> = {};
  for (const [key, value] of Object.entries(host.styles?.variables ?? {})) {
    const source = key.replace(/^--/, "");
    const names = aliases[source] ?? [source];
    for (const name of names) if (safe(name, value)) values[name] = value;
  }
  // An explicit adopter theme wins over the host palette. Dark values override
  // common/light tokens, so shared typography and radius also apply in dark mode.
  for (const [name, value] of Object.entries({
    ...theme.light,
    ...(dark ? theme.dark : {}),
  })) {
    if (safe(name, value)) values[name] = value;
  }
  for (const name of applied) element.style.removeProperty("--" + name);
  applied = new Set(Object.keys(values));
  for (const [name, value] of Object.entries(values))
    element.style.setProperty("--" + name, value);
}
