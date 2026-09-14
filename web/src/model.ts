export type Entry = {
  title: string;
  before?: string;
  after?: string;
  message?: string;
};
export type View = {
  headline: string;
  subject: string;
  counts: string;
  status: string;
  scope: string;
  entries: Entry[];
  action: string;
};
const text = (value: any) =>
  typeof value === "string" ? value : JSON.stringify(value);
const noun = (n: number, singular: string) =>
  `${n} ${singular}${n === 1 ? "" : "s"}`;
const valueText = (value: any) =>
  value == null
    ? "None"
    : value.preview +
      (value.truncated
        ? `\nPreview · ${value.characters} characters in full value`
        : "");
const receiptEntries = (receipt: any) => {
  const result: Entry[] = [],
    body = receipt.body_change;
  const title =
    receipt.after?.identifier ?? receipt.before?.identifier ?? "Knowledge";
  if (body?.kind === "grouped_exact_replacement") {
    for (const [index, item] of body.replacements.entries()) {
      if (item.before?.sha256 !== item.after?.sha256)
        result.push({
          title: `${title} · Passage ${index + 1}`,
          before: valueText(item.before),
          after: valueText(item.after),
        });
    }
  } else if (body && body.before?.sha256 !== body.after?.sha256) {
    result.push({
      title: `${title} · Content`,
      before: valueText(body.before),
      after: valueText(body.after),
    });
  }
  for (const change of receipt.metadata_changes ?? []) {
    result.push({
      title: `${title} · ${change.key}`,
      before: change.before_present === false ? "Absent" : text(change.before),
      after: change.after_present === false ? "Absent" : text(change.after),
    });
  }
  if (receipt.operation.startsWith("move"))
    result.push({
      title: "Location",
      before: receipt.before?.identifier,
      after: receipt.after?.identifier,
    });
  return result;
};
const isChanged = (receipt: any) =>
  receipt.operation.startsWith("move") ||
  receipt.before?.content_sha256 !== receipt.after?.content_sha256 ||
  (receipt.metadata_changes?.length ?? 0) > 0;

export function describe(output: any = {}, isError = false): View {
  const view: View = {
    headline: "",
    subject: "",
    counts: "",
    status: "",
    scope:
      "This operation only. Other tools and direct edits are outside this receipt.",
    entries: [],
    action: "View changes",
  };
  let entries: Entry[] = [];
  try {
    const receipt = output.knowledge_change;
    const completed = Array.isArray(output.completed) ? output.completed : null;
    if (isError) {
      view.headline = "Operation failed";
      view.status =
        "A write may have committed. Inspect current state before retrying.";
      entries = [
        {
          title: "Error",
          message:
            (output.content ?? [])
              .filter((x: any) => x.type === "text")
              .map((x: any) => x.text)
              .join("\n") || "No successful change receipt was returned.",
        },
      ];
    } else if (output.preview) {
      view.headline = "Preview · nothing saved";
      view.subject = output.identifier ?? "";
      entries = [
        { title: "Proposed content", message: output.proposed_content ?? "" },
      ];
    } else if (receipt) {
      const changed = isChanged(receipt);
      const names: Record<string, string> = {
        create: "Note created",
        edit: "Note updated",
        revise: "Note revised",
        move_note: "Note moved",
        move_namespace: "Namespace moved",
        remove_note: "Note removed",
      };
      view.headline = output.replayed
        ? "Previously completed"
        : changed
          ? (names[receipt.operation] ?? "Knowledge updated")
          : "No content changes";
      view.subject =
        receipt.after?.identifier ?? receipt.before?.identifier ?? "";
      entries = receiptEntries(receipt);
      const n = receipt.affected_notes;
      const count =
        receipt.affected_notes_exact && Number.isInteger(n)
          ? noun(n, "note")
          : "Note count not reported";
      view.counts = `${count} · ${noun(entries.length, "change")}`;
      view.status = receipt.readback_verified
        ? "Saved result checked"
        : "Backend confirmed";
      if (output.replayed) view.status = "Earlier result · no new write";
      view.scope = receipt.coverage_notice;
    } else if (completed) {
      const fresh = completed.filter(
        (item: any) => !item.replayed && item.knowledge_change,
      );
      const changed = fresh.filter((item: any) =>
        isChanged(item.knowledge_change),
      );
      const replayed = completed.filter((item: any) => item.replayed).length;
      const missing = completed.filter(
        (item: any) => !item.replayed && !item.knowledge_change,
      ).length;
      const errors = output.errors ?? [];
      view.headline =
        output.partial || errors.length
          ? "Maintenance partially completed"
          : changed.length
            ? "Knowledge updated"
            : "No new changes";
      view.counts =
        `${noun(changed.length, "note")} changed` +
        (replayed ? ` · ${replayed} previously completed` : "") +
        (errors.length ? ` · ${noun(errors.length, "error")}` : "") +
        (missing ? ` · ${missing} outcomes without receipts` : "");
      entries = fresh.flatMap((item: any) =>
        receiptEntries(item.knowledge_change),
      );
      entries.push(
        ...errors.map((error: any) => ({
          title: error.identifier ?? error.record_id ?? "Error",
          message: error.error,
        })),
      );
      view.status =
        output.partial || errors.length
          ? "Inspect failed items before retrying."
          : "Maintenance result checked";
    } else if (output.replayed) {
      view.headline = "Previously completed";
      view.status = "Earlier result · no new write";
    } else {
      view.headline = "No change receipt returned";
      view.status = "Inspect the tool result before claiming a saved change.";
    }
  } catch (_) {
    view.headline = "Result could not be displayed";
    view.status = "Inspect the tool result before claiming a saved change.";
    entries = [];
    view.subject = "";
    view.counts = "";
  }
  for (const key of [
    "headline",
    "subject",
    "counts",
    "status",
    "scope",
  ] as const)
    view[key] = text(view[key]) ?? "";
  if (output?.knowledge_change && typeof view.subject === "string") {
    const prefix = view.subject + " · ";
    entries = entries.map((item) => ({
      ...item,
      title:
        typeof item.title === "string" && item.title.startsWith(prefix)
          ? item.title.slice(prefix.length)
          : item.title,
    }));
  }
  view.entries = entries.map((item) => ({
    title: text(item.title),
    before: text(item.before),
    after: text(item.after),
    message: text(item.message),
  }));
  if (isError) view.action = "View error";
  else if (output?.preview) view.action = "View preview";
  else if (!entries.length) view.action = "View details";
  return view;
}
