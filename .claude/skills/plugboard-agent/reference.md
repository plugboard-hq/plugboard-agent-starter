# Plugboard core API, as an agent sees it

Signatures from `plugboard` core. Only these are part of the contract.

## Manifest

```python
from plugboard import AgentManifest, register

register(AgentManifest(
    name="weather",                 # call_weather
    title="Weather",
    routing_description="...",      # for the supervisor
    persona="...",                  # for the worker
    tools=make_tools,               # () -> list[Callable]
    requires=[],                    # provider instance names
    examples=["...", "..."],
    source="https://github.com/plugboard-hq/plugboard-weather",
    config_schema={"type": "object", "properties": {...}},  # optional
    max_iters=4,
))
```

Settings: `registry.get("weather").settings` is the schema defaults overlaid
with what the console saved. Read it inside the tool body.

## Capabilities

```python
from plugboard.capabilities import ask_user, database_tools
AgentManifest(..., capabilities=[database_tools(lambda: registry.get("<name>").settings, agent="<name>"), ask_user()])
```

`database_tools` reads `provider` (default `warehouse`), `row_limit` and `show_rows` from the
settings it is given, at call time. `identity_tools(settings)` (default provider `directory`)
gives `who_am_i`, `find_people`, `members_of` over an Identity provider; `git_tools(settings)`
(default provider `repos`, `commit_limit`) gives `list_repositories`, `recent_commits`,
`list_files`, `read_file` over a Git provider. In a skill file: `identity_tools: { provider:
directory }`, `git_tools: { provider: repos }`. Each capability carries its own usage notes, appended to
the persona. Bespoke widget kinds are the agent's: subclass `plugboard.widgets.Widget` in the
agent's package and render them in its pane (core renders only table and question).

## Turn context

```python
from plugboard.turn import current_turn
turn = current_turn()
turn.tool_call(tool: str, args: dict, summary: str)   # one per call; shown in the trail
turn.show(widget)                                     # display widget, returns at once
answer: str = turn.ask(QuestionWidget(prompt=..., options=[...]))  # blocks for the user
turn.artifacts.publish(Dataset(...)) -> Dataset       # .id is "ds_<n>" in this conversation
turn.artifacts.list() -> list[Dataset]
turn.artifacts.get("ds_1") -> Dataset | None
```

## Widgets

```python
from plugboard.widgets import TableWidget, ChartWidget, QuestionWidget
TableWidget(title=, columns=[...], rows=[[...]], total_rows=, dataset_id=, sql=)
ChartWidget(title=, chart_type="bar"|"hbar"|"line"|"pie", categories=[...],
            series=[{"name": str, "values": [...]}], x_label=, y_label=, dataset_id=)
QuestionWidget(prompt=, options=[...])   # blocking; use through turn.ask
```

## Datasets

```python
from plugboard.artifacts import Dataset
Dataset(title=, columns=[...], rows=[[...]], sql="", created_by="<agent name>")
```

Publish the full rows; the UI shows a capped view and other agents fetch by id.

## Providers

```python
from plugboard.providers import providers
db = providers.get("warehouse")     # a Database: .schema(), .describe(table), .select(sql, limit)
```

`select` accepts one SELECT or WITH statement and adds a LIMIT; anything else
raises `QueryRejected`. Declare the instance name in `requires`.

## Packaging

`pyproject.toml` with hatchling, `packages = ["<package>"]`, no dependency on
`plugboard` (the host provides it). Install into a host with
`uv add --group agents <path-or-git-url>` and name the package in
`PLUGBOARD_EXTRA_AGENTS`.

## Frontend bundle

```js
// src/index.jsx — the whole contract with the host
import { createRoot } from "react-dom/client";
const COMPONENTS = { MyPane };
const roots = new WeakMap();
export function mount(el, ctx) {           // idempotent; ctx.component names the component
  let root = roots.get(el); if (!root) { root = createRoot(el); roots.set(el, root); }
  const C = COMPONENTS[ctx.component]; root.render(<C {...ctx} />);
}
export function unmount(el) { roots.get(el)?.unmount(); roots.delete(el); }
```

```js
// vite.config.js — library build, externals left to the host's import map
build: { lib: { entry: "src/index.jsx", formats: ["es"], fileName: () => "<name>.js" },
         outDir: "../<package>/static", emptyOutDir: true,
         rollupOptions: { external: ["react", "react-dom", "react/jsx-runtime", "react-dom/client", "@plugboard/sdk"] } }
```

`@plugboard/sdk` exports: `Pane({ title, subtitle, icon, tabs, tab, onTab, actions, onClose, children })`,
`TableView({ widget, bare })`, `ChartView({ widget, bare })`, `SqlView({ sql })`, `call(path, init)`,
`useDataset(conversationUuid, id)`, `useSchema(providerName)`, `useProviders()`,
`runQuery(conversationUuid, { sql, provider, title, via })`, `refreshConversation()`,
`openArtifact(conversationUuid, id)`, `prefill(text)`.

Surfaces on the manifest: `{"kind": "artifact", "component": "MyPane", "title": "..."}` renders
this agent's datasets; `{"kind": "badge", "key": "...", "title": "...", "icon": "database",
"component": "MyPane"}` adds a header badge that opens a pane.

## Skill agent file

```markdown
---
name: inventory
title: Inventory
routing_description: >
  Stock questions ... Use for 'stock', 'inventory', 'reorder'. For revenue use the data agent.
requires: [warehouse]
capabilities:
  - database_tools: { provider: warehouse, row_limit: 50, show_rows: 20 }
  - ask_user
examples: ["which products are below their reorder point?"]
settings:
  provider: { type: string, title: Database provider, default: warehouse }
max_iters: 6
---
The persona: what the agent answers, domain facts it should know, what the user already
sees, how long the result should be.
```

From a package: `register_skill(Path(__file__).parent / "SKILL.md", source=..., frontend=..., surfaces=[...])`.
Known capabilities: `database_tools`, `ask_user` (`plugboard.skills.CAPABILITIES`).
