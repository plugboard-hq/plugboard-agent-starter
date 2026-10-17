#!/usr/bin/env python3
"""Scaffold a Plugboard agent package.

    python new_agent.py <name> --title "<Title>" [--out ../plugboard-<name>] [--requires warehouse]

Writes a package `plugboard_<name>` with a manifest, one example tool that
publishes a dataset and shows it, a README and a pyproject. Edit the routing
description, persona and tool; the shape is what matters.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="snake_case agent name, e.g. jira")
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", help="directory to create (default ../plugboard-<name>)")
    ap.add_argument("--requires", default="", help="comma-separated provider names")
    ap.add_argument("--source", default="", help="repository URL for the manifest")
    ap.add_argument("--frontend", action="store_true", help="also scaffold a frontend bundle")
    ap.add_argument("--skill", action="store_true", help="scaffold a SKILL.md agent (no code) instead")
    a = ap.parse_args()
    if not re.match(r"^[a-z][a-z0-9_]*$", a.name):
        raise SystemExit("name must be snake_case")
    if a.skill:
        write_skill(a)
        return
    pkg = f"plugboard_{a.name}"
    out = Path(a.out or f"../plugboard-{a.name.replace('_', '-')}").resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty")
    (out / pkg).mkdir(parents=True)
    requires = [r.strip() for r in a.requires.split(",") if r.strip()]
    dist = out.name

    (out / "pyproject.toml").write_text(f'''[project]
name = "{dist}"
version = "0.1.0"
description = "{a.title} agent for Plugboard."
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["{pkg}"]

[tool.ruff]
line-length = 99
target-version = "py312"
''')

    path_import = "from pathlib import Path\n\n" if a.frontend else ""
    frontend_lines = (
        f'\n        frontend=str(Path(__file__).parent / "static" / "{a.name}.js"),'
        f'\n        surfaces=[{{"kind": "artifact", "component": "{pascal(a.name)}Pane", "title": "{a.title}"}}],'
        if a.frontend
        else ""
    )
    (out / pkg / "__init__.py").write_text(f'''"""{a.title} agent for Plugboard.

Importing this package registers the manifest; the host names it in
PLUGBOARD_EXTRA_AGENTS. Nothing else happens at import time.
"""

{path_import}from plugboard import AgentManifest, register

from {pkg}.tools import make_tools

register(
    AgentManifest(
        name="{a.name}",
        title="{a.title}",
        routing_description=(
            "TODO: what this agent answers, the phrases a user would use "
            "('...', '...'), what to pass in, what comes back, and what it cannot do."
        ),
        persona=(
            "TODO: the method in order, how to use each tool, what the user already "
            "sees (so the result is a short summary), what to do when something is "
            "missing. Never invent data."
        ),
        tools=make_tools,
        requires={requires!r},
        examples=["TODO: a prompt as the user would type it", "TODO: another"],
        source="{a.source}",{frontend_lines}
        config_schema={{
            "type": "object",
            "properties": {{
                "limit": {{
                    "type": "integer",
                    "title": "Row limit",
                    "description": "Most rows the example tool returns",
                    "default": 20,
                }},
            }},
        }},
        max_iters=4,
    )
)
''')

    (out / pkg / "tools.py").write_text(f'''"""Tools for the {a.title} agent.

Every tool reads the turn through ``current_turn()``: it records one
``tool_call`` summary on every path, shows results as widgets, publishes rows
as datasets so other agents can use them by id, and returns plain text the
model can act on. Expected failures are returned, not raised.
"""

from __future__ import annotations

from collections.abc import Callable

from plugboard.artifacts import Dataset
from plugboard.registry import registry
from plugboard.turn import current_turn
from plugboard.widgets import TableWidget


def _settings() -> dict:
    """Settings are read at call time; the console may have changed them."""
    return registry.get("{a.name}").settings


def make_tools() -> list[Callable]:
    def example(query: str) -> str:
        """TODO: one sentence the model reads to decide when to call this, what
        `query` is, and what comes back."""
        turn = current_turn()
        limit = int(_settings().get("limit", 20))
        try:
            rows = [[query, i] for i in range(1, 4)][:limit]  # TODO: the real work
        except Exception as exc:  # noqa: BLE001 - expected failures are returned as text
            turn.tool_call("example", {{"query": query}}, f"failed: {{exc}}")
            return f"failed: {{exc}}"
        dataset = turn.artifacts.publish(
            Dataset(title=f"Example for {{query}}", columns=["query", "n"], rows=rows,
                    created_by="{a.name}")
        )
        turn.tool_call("example", {{"query": query}}, f"{{len(rows)}} rows -> dataset {{dataset.id}}")
        turn.show(TableWidget(title=dataset.title, columns=dataset.columns, rows=rows,
                              total_rows=len(rows), dataset_id=dataset.id))
        return f"dataset {{dataset.id}} with {{len(rows)}} rows: {{rows}}"

    return [example]
''')

    (out / "README.md").write_text(f'''# {dist}

{a.title} agent for [Plugboard](https://github.com/plugboard-hq/plugboard). One package,
one manifest, a `make_tools()` factory; it depends on Plugboard's core and on nothing
else in the host.

## What it does

TODO: what it answers, what it publishes, and the two example prompts from the manifest.

## Install into a Plugboard host

```
cd plugboard
uv add --group agents git+https://github.com/plugboard-hq/{dist}    # or a path: ../{dist}
echo 'PLUGBOARD_EXTRA_AGENTS={pkg}' >> .env                       # comma-separated with others
uv run uvicorn project.asgi:application --port 8010
```

The host imports the package at start-up; importing registers the manifest. The agent
then appears on the board and in the console with its settings form rendered from
`config_schema`.

## Settings

| Setting | Default | What it does |
|---|---|---|
| `limit` | 20 | Most rows the example tool returns |

## Build your own agent

[plugboard-sdk](https://github.com/plugboard-hq/plugboard-sdk) holds the contract, the
frontend SDK and a Claude Code skill that scaffolds and checks an agent against it.

## Layout

```
{pkg}/
  __init__.py   the manifest; importing registers it
  tools.py      make_tools() and the tools
```
''')
    (out / ".gitignore").write_text("__pycache__/\n*.pyc\n.venv/\ndist/\n.ruff_cache/\nfrontend/node_modules/\n")
    if a.frontend:
        write_frontend(out, pkg, a.name, a.title)
    print(f"wrote {out}")
    print(f"next: edit {pkg}/__init__.py and {pkg}/tools.py, then install into a host")


def write_skill(a) -> None:
    """A skill agent: one SKILL.md in <out>/<name>/ (default ./skills/<name>/)."""
    out = Path(a.out or f"skills/{a.name}").resolve()
    out.mkdir(parents=True, exist_ok=True)
    requires = [r.strip() for r in a.requires.split(",") if r.strip()]
    caps = "\n".join(f"  - database_tools: {{ provider: {r}, row_limit: 50, show_rows: 20 }}" for r in requires) or "  # - database_tools: { provider: warehouse }"
    (out / "SKILL.md").write_text(f'''---
name: {a.name}
title: {a.title}
routing_description: >
  TODO: what this agent answers, the phrases a user would use ('...', '...'), what to
  pass in, what comes back, and which other agent to use instead for neighbouring questions.
requires: {requires}
capabilities:
{caps}
  - ask_user
examples:
  - TODO: a prompt as the user would type it
  - TODO: another
settings:
  provider: {{ type: string, title: Database provider, default: {requires[0] if requires else "warehouse"} }}
max_iters: 6
---
TODO: the persona. What the agent answers, the domain facts it should know (tables,
definitions), what the user already sees (so the result is a short summary with the key
numbers and the dataset id), and what to do when something is missing. Never invent data.
''')
    print(f"wrote {out / 'SKILL.md'}")
    print("next: fill in the TODOs; the host loads skills/*/SKILL.md on restart")


def pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def write_frontend(out: Path, pkg: str, name: str, title: str) -> None:
    """A Vite library build against @plugboard/sdk with one pane component."""
    fe = out / "frontend" / "src"
    fe.mkdir(parents=True)
    comp = f"{pascal(name)}Pane"
    (out / "frontend" / "package.json").write_text(f'''{{
  "name": "{out.name}-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {{ "build": "vite build", "watch": "vite build --watch" }},
  "devDependencies": {{ "@vitejs/plugin-react": "^4.3.4", "vite": "^6.0.0" }}
}}
''')
    (out / "frontend" / "vite.config.js").write_text(f'''import {{ defineConfig }} from "vite";
import react from "@vitejs/plugin-react";

// Library build: one ESM file; React and the Plugboard SDK stay bare imports
// that the host's import map resolves to its own instances.
export default defineConfig({{
  plugins: [react()],
  build: {{
    lib: {{ entry: "src/index.jsx", formats: ["es"], fileName: () => "{name}.js" }},
    outDir: "../{pkg}/static",
    emptyOutDir: true,
    rollupOptions: {{ external: ["react", "react-dom", "react/jsx-runtime", "react-dom/client", "@plugboard/sdk"] }},
  }},
}});
''')
    (fe / "index.jsx").write_text(f'''import {{ createRoot }} from "react-dom/client";
import {comp} from "./{comp}.jsx";

/** mount(el, ctx) / unmount(el): the whole contract with the host. */
const COMPONENTS = {{ {comp} }};
const roots = new WeakMap();

export function mount(el, ctx) {{
  const Component = COMPONENTS[ctx.component];
  let root = roots.get(el);
  if (!root) {{
    root = createRoot(el);
    roots.set(el, root);
  }}
  root.render(Component ? <Component {{...ctx}} /> : <div style={{{{ padding: 16 }}}}>Unknown component {{ctx.component}}</div>);
}}

export function unmount(el) {{
  const root = roots.get(el);
  if (root) {{
    root.unmount();
    roots.delete(el);
  }}
}}
''')
    (fe / f"{comp}.jsx").write_text(f'''import {{ Pane, TableView }} from "@plugboard/sdk";

/**
 * {title}'s own view of a dataset it produced. ctx brings artifact, dataset,
 * conversationUuid, agentTitle and onClose. Style with the theme's CSS
 * variables; the host's Tailwind classes are not compiled for bundles.
 */
export default function {comp}({{ artifact, dataset, agentTitle, onClose }}) {{
  const rows = dataset?.rows || [];
  return (
    <Pane title={{artifact.title}} subtitle={{`${{agentTitle || "{title}"}} · ${{artifact.id}} · ${{rows.length}} rows`}} onClose={{typeof onClose === "function" ? onClose : undefined}}>
      {{!dataset && <div style={{{{ padding: "16px 20px", color: "var(--color-muted)", fontSize: 14 }}}}>Loading…</div>}}
      {{dataset && <TableView widget={{{{ ...dataset, total_rows: rows.length }}}} bare />}}
    </Pane>
  );
}}
''')
    (out / pkg / "static").mkdir(exist_ok=True)
    (out / pkg / "static" / ".gitkeep").write_text("")
    print(f"frontend: cd {out.name}/frontend && npm install && npm run build")


if __name__ == "__main__":
    main()
