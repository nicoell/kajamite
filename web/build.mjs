import { build } from "esbuild";
import { readFile, writeFile, readdir, mkdtemp, rm } from "node:fs/promises";
import { createHash } from "node:crypto";
import { gzipSync } from "node:zlib";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import os from "node:os";
const web = path.dirname(fileURLToPath(import.meta.url)),
  root = path.dirname(web);
process.chdir(web);
const check = process.argv.includes("--check");
const temporary = await mkdtemp(path.join(os.tmpdir(), "kajamite-ui-build-"));
const hash = (data) => createHash("sha256").update(data).digest("hex");
const inputs = {};
async function sources(directory) {
  for (const entry of (await readdir(directory, { withFileTypes: true })).sort(
    (a, b) => (a.name < b.name ? -1 : 1),
  )) {
    if (entry.name === "node_modules") continue;
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) await sources(file);
    else
      inputs[path.relative(root, file).split(path.sep).join("/")] = hash(
        (await readFile(file, "utf8")).replace(/\r\n/g, "\n"),
      );
  }
}
try {
  const cssFile = path.join(temporary, "style.css");
  const cssBuild = spawnSync(
    process.execPath,
    [
      "node_modules/@tailwindcss/cli/dist/index.mjs",
      "-i",
      "src/style.css",
      "-o",
      cssFile,
      "--minify",
    ],
    { encoding: "utf8" },
  );
  if (cssBuild.status !== 0)
    throw Error(cssBuild.stderr || "Tailwind build failed");
  const js = await build({
    entryPoints: ["src/app.tsx"],
    bundle: true,
    minify: true,
    write: false,
    metafile: true,
    format: "iife",
    target: "es2022",
    define: { "process.env.NODE_ENV": '"production"' },
    legalComments: "inline",
  });
  const css = (await readFile(cssFile, "utf8")).trim();
  const javascript = js.outputFiles[0].text
    .trim()
    .replace(/<\/script/gi, "<\\/script");
  const html = (await readFile("template.html", "utf8"))
    .replace(/\r\n/g, "\n")
    .replace("__KAJAMITE_CSS__", () => css)
    .replace("__KAJAMITE_JS__", () => javascript);
  const packages = new Map();
  for (const source of Object.keys(js.metafile.inputs)) {
    if (!source.startsWith("node_modules/")) continue;
    let dir = path.dirname(source);
    while (dir !== "node_modules" && dir !== ".") {
      try {
        const pkg = JSON.parse(
          await readFile(path.join(dir, "package.json"), "utf8"),
        );
        if (pkg.name) {
          packages.set(pkg.name, { dir, pkg });
          break;
        }
      } catch (_) {}
      dir = path.dirname(dir);
    }
  }
  let notices =
    "Bundled UI notices\n\nshadcn/ui source\n" +
    (await readFile("SHADCN-LICENSE.txt", "utf8"));
  for (const [name, { dir, pkg }] of [...packages].sort(([a], [b]) =>
    a < b ? -1 : 1,
  )) {
    const files = await readdir(dir);
    const license = files.find((n) => /^license(?:\.md|\.txt)?$/i.test(n));
    if (!license) throw Error("Missing license for " + name);
    notices +=
      "\n\n" +
      name +
      " " +
      pkg.version +
      "\n" +
      (await readFile(path.join(dir, license), "utf8"));
  }
  notices = notices.replace(/\r\n/g, "\n");
  const outputs = {
    "src/kajamite/knowledge-change.html": html,
    "src/kajamite/UI-NOTICES.txt": notices,
  };
  await sources(web);
  const manifest = {
    schema_version: 1,
    inputs,
    outputs: Object.fromEntries(
      Object.entries(outputs).map(([name, text]) => [name, hash(text)]),
    ),
  };
  outputs["src/kajamite/ui-build.json"] =
    JSON.stringify(manifest, null, 2) + "\n";
  for (const [name, text] of Object.entries(outputs)) {
    const destination = path.join(root, name);
    if (check) {
      if ((await readFile(destination, "utf8")).replace(/\r\n/g, "\n") !== text)
        throw Error("Stale UI artifact: " + name + "; run npm run build");
    } else await writeFile(destination, text);
  }
  console.log(
    `UI ${check ? "verified" : "built"}: ${Buffer.byteLength(html)} bytes (${gzipSync(html).length} gzip bytes); no runtime asset downloads`,
  );
} finally {
  await rm(temporary, { recursive: true, force: true });
}
