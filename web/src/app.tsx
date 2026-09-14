import { useEffect, useState, useSyncExternalStore } from "react";
import { createRoot } from "react-dom/client";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { Separator } from "@/components/ui/separator";
import { createBridge } from "./bridge";
import { describe } from "./model";
const theme = JSON.parse(
  document.getElementById("kajamite-theme")!.textContent!,
);
const bridge = createBridge(theme);
function Evidence({ result }: { result: any }) {
  const [open, setOpen] = useState(false);
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" id="evidence-toggle">
          Technical evidence
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent id="evidence">
        <pre
          id="raw"
          className="break-anywhere whitespace-pre-wrap font-mono text-xs"
        >
          {JSON.stringify(result, null, 2)}
        </pre>
      </CollapsibleContent>
    </Collapsible>
  );
}
function App() {
  const state = useSyncExternalStore(bridge.subscribe, bridge.snapshot);
  const view = describe(state.result, state.error);
  const waiting = state.stage === "waiting",
    working = state.stage === "working";
  const headline = waiting
    ? "Waiting for result"
    : working
      ? "Working"
      : state.stage === "cancelled"
        ? "Operation cancelled"
        : view.headline;
  useEffect(() => {
    const observer = new ResizeObserver(bridge.resize);
    observer.observe(document.body);
    return () => observer.disconnect();
  }, []);
  useEffect(() => bridge.resize(), [state]);
  return (
    <main aria-label="Knowledge operation result">
      <Card className="gap-3 py-4">
        <CardHeader className="gap-1 px-4">
          <CardTitle>
            <h1 id="headline" role="status">
              {headline}
            </h1>
          </CardTitle>
          <CardDescription id="subject" className="line-clamp-2 break-anywhere">
            {view.subject}
          </CardDescription>
          <p id="counts" className="text-sm text-muted-foreground">
            {view.counts}
          </p>
        </CardHeader>
        <Collapsible open={state.expanded} onOpenChange={bridge.toggle}>
          <CardContent className="px-4">
            <div id="actions" hidden={waiting || working}>
              <CollapsibleTrigger asChild>
                <Button variant="outline" id="toggle">
                  {state.expanded ? "Hide details" : view.action}
                </Button>
              </CollapsibleTrigger>
            </div>
            <CollapsibleContent id="review">
              <div id="changes" className="flex flex-col gap-4 pt-4">
                {view.entries.slice(0, state.visible).map((item, index) => (
                  <section key={index} className="flex flex-col gap-3">
                    <Separator />
                    <h2 className="break-anywhere text-sm font-medium">
                      {item.title}
                    </h2>
                    {item.message !== undefined ? (
                      <pre className="break-anywhere whitespace-pre-wrap text-sm">
                        {item.message}
                      </pre>
                    ) : (
                      <div className="comparison grid grid-cols-2 gap-4">
                        {[
                          ["Previous", item.before],
                          ["Current", item.after],
                        ].map(([label, value]) => (
                          <div
                            key={label}
                            className="min-w-0 flex flex-col gap-1"
                          >
                            <p className="text-xs text-muted-foreground">
                              {label}
                            </p>
                            <pre className="break-anywhere whitespace-pre-wrap text-sm">
                              {value ?? "None"}
                            </pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                ))}
              </div>
              <div className="flex flex-col items-start gap-3 pt-4">
                <Button
                  id="more"
                  variant="secondary"
                  hidden={state.visible >= view.entries.length}
                  onClick={bridge.showMore}
                >
                  Show more ({Math.max(0, view.entries.length - state.visible)}{" "}
                  remaining)
                </Button>
                <p id="scope" className="text-xs text-muted-foreground">
                  {view.scope}
                </p>
                <Evidence key={state.generation} result={state.result} />
              </div>
            </CollapsibleContent>
          </CardContent>
        </Collapsible>
        <CardFooter className="px-4">
          <p id="status" className="text-xs text-muted-foreground">
            {state.disconnected
              ? "Waiting for the host. The tool result remains available in chat."
              : waiting || working
                ? ""
                : view.status}
          </p>
        </CardFooter>
      </Card>
    </main>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
