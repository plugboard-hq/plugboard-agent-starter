# plugboard-agent-starter

Start here to build an agent for [Plugboard](https://github.com/plugboard-hq/plugboard).
Use this repository as a GitHub template, or clone it, and you have a working agent with a
manifest, one tool, a pane of its own and a Claude Code skill that knows the contract. Fill
in the TODOs, install it into a host, and the supervisor can route to it.

Two kinds of agent live here, by choice not by type. Keep the one you need.

| | Skill agent | Package agent |
|---|---|---|
| What it is | `skill-agent-example/SKILL.md`: frontmatter for the manifest, body for the persona, `capabilities` naming what it takes from core | `plugboard_starter/`: Python with its own tools and, in `frontend/`, its own pane |
| Right when | the agent is a persona over existing capabilities (`database_tools`, `identity_tools`, `git_tools`, `ask_user`) | no capability does the job, or the agent needs its own screen |
| Code | none | a manifest, `make_tools()`, optional React pane |

Start with the skill agent; promote to a package only when you write a tool.

## What an agent is

A Python package that calls `register(AgentManifest(...))` at import and does nothing else
at import time. The host imports the package because it is named in `PLUGBOARD_EXTRA_AGENTS`;
importing registers the manifest, and from then on the supervisor can route to it. The
package depends on `plugboard` core and on nothing else in the host, so it cannot reach
into another agent.

```python
from plugboard import AgentManifest, register

register(AgentManifest(
    name="starter",                 # the supervisor's tool is call_starter
    title="Starter",                # one or two words for the board
    routing_description="...",      # for the supervisor: what it answers, the user's phrases, what it cannot do
    persona="...",                  # for the worker: method, tools, what the user already sees
    tools=make_tools,               # () -> list[Callable], called once per turn
    capabilities=[...],             # tool sets taken from core, with their usage notes
    requires=[],                    # provider instance names the tools reach for, e.g. ["warehouse"]
    examples=["...", "..."],        # two prompts as a user would type them; quick starts and routing tests
    source="https://github.com/<org>/plugboard-<name>",
    config_schema={...},            # JSON schema; the console renders the settings form from it
    frontend="…/static/<name>.js",  # optional: the agent's own pane
    surfaces=[...],                 # what that pane renders
    max_iters=4,
))
```

Each tool: one docstring the model reads, typed arguments, a `turn.tool_call(...)` summary
on every path including failure, and a plain-text return. Show results with widgets;
publish rows as datasets so other agents can use them by id. Expected failures are
returned as text, never raised.

## Make it yours

1. Rename. `starter` appears in `pyproject.toml`, the package directory
   `plugboard_starter/`, the manifest (`name`, `title`), `frontend/vite.config.js` (the
   output file and directory) and `frontend/src/index.jsx` (the component map). Choose a
   snake_case name; the supervisor's tool becomes `call_<name>`.
2. Write the routing description first. It is what the supervisor's tool says about
   itself: what the agent answers, the phrases a user would use, what to pass in, what
   comes back, and what it cannot do.
3. Write the tools, or take capabilities. Shared behaviour (warehouse access, the
   directory, repositories, asking the user) comes from `plugboard.capabilities`; write a
   tool only for what no capability does.
4. If you keep the pane: `cd frontend && npm install && npm run build` writes
   `plugboard_starter/static/<name>.js`. Commit the built file so a host needs no Node.
   Delete `frontend/` and the `frontend`/`surfaces` lines on the manifest if you do not.
5. Install into a host and try every example prompt:
   ```
   cd plugboard
   uv add --group agents ../plugboard-<name>          # or git+https://github.com/<org>/plugboard-<name>
   echo 'PLUGBOARD_EXTRA_AGENTS=plugboard_<name>' >> .env
   uv run uvicorn project.asgi:application --port 8010
   uv run python tests/stream_smoke.py "<first example prompt>"
   ```
   A skill agent instead: `echo 'PLUGBOARD_EXTRA_SKILLS=../plugboard-<name>' >> .env`, with
   `SKILL.md` at the repository root.

## The pane

The host exposes `@plugboard/sdk` and an import map that points `react`, `react-dom` and
`@plugboard/sdk` at the host's own instances, so `frontend/` is a small Vite library build
with those as externals: one ESM file the host serves and mounts through `mount(el, ctx)`
and `unmount(el)`. `ctx.component` names which component to render; for an `artifact`
surface ctx also carries `artifact`, `dataset`, `conversationUuid`, `agentTitle` and
`onClose`. Compose `Pane`, `TableView` and `SqlView` from the SDK so the pane sits in the
shell like the host's own, and style with the theme's CSS variables (`--color-ink`,
`--color-muted`, `--color-line`, `--color-paper`, `--color-surface`, `--color-accent`,
`--font-mono`); the host's Tailwind classes are not compiled for bundles.

On the manifest, `surfaces` say what the pane renders: `{"kind": "artifact", "component":
"StarterPane"}` takes over the pane for this agent's datasets (add `"when": "sql"` to apply
to any dataset that carries SQL); `{"kind": "badge", "key": "...", "icon": "...", "title":
"..."}` adds a header badge that opens a pane.

The SDK's exports and the exact core signatures are in
[plugboard-sdk](https://github.com/plugboard-hq/plugboard-sdk).

## Build it with Claude Code

`.claude/skills/plugboard-agent` is a copy of the SDK's skill. Open this repository in
Claude Code and ask for the agent you want: it fills in the manifest and tools to the
contract, installs into a host and runs the example prompts. The checklist at the end of
the skill is what "done" means. The canonical copy lives in plugboard-sdk; this one is
here so the template works on its own.

## Worked examples

- [plugboard-weather](https://github.com/plugboard-hq/plugboard-weather): one tool, its own pane.
- [plugboard-genbi](https://github.com/plugboard-hq/plugboard-genbi): a charts agent and a SQL workbench pane.
- [plugboard-inventory](https://github.com/plugboard-hq/plugboard-inventory): a skill agent, one `SKILL.md`.
