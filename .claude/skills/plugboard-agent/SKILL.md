---
name: plugboard-agent
description: Build, review or fix an agent for Plugboard (the supervisor you plug agents into). Use when asked to create a new Plugboard agent, add a tool to one, make an agent's manifest routable, publish datasets or widgets from a tool, or check an agent against the Plugboard contract before installing it into a host.
---

# Building a Plugboard agent

An agent is a Python package with one job: register a manifest. The supervisor
reads the manifest to decide when to delegate; the worker runs the agent's
persona and tools; the UI shows what the tools emit. This repository holds the
contract and the frontend SDK; the reference agent is
[plugboard-weather](https://github.com/plugboard-hq/plugboard-weather): read its
`plugboard_weather/__init__.py` and `plugboard_weather/tools.py` before writing
anything, and keep the same shape. `README.md` here is the contract in prose;
`reference.md` in this skill is the exact signatures.

## Two kinds of agent

- **Skill agent**: a `SKILL.md`, no code. Frontmatter for the manifest, body for the
  persona, `capabilities` naming what it takes from core. Right when the agent is a
  persona over existing capabilities (a data question, a stock question). Drop it in
  the host's `skills/<name>/` or register it from a package with `register_skill`.
  Scaffold: `python .claude/skills/plugboard-agent/scripts/new_agent.py <name> --title "<Title>" --skill`.
- **Package agent**: Python with its own tools, optional frontend bundle. Right when
  no capability does the job or the agent needs its own UI. The procedure below.

Start with a skill agent; promote to a package only when you write a tool.

## Procedure

1. **Name the job in one sentence.** If it needs two sentences it is two
   agents. The supervisor composes agents; agents do not compose each other.
2. **Scaffold.** `python .claude/skills/plugboard-agent/scripts/new_agent.py <name> --title "<Title>" --out ../plugboard-<name>`
   gives a package, manifest, one example tool, README and `pyproject.toml`.
3. **Write the manifest** (see the contract below). The routing description is
   the most important text in the package: it is what the supervisor's
   `call_<name>` tool says about itself.
4. **Write the tools.** Each tool: one docstring the model will read, typed
   arguments, a `turn.tool_call(...)` summary on every path including failure,
   and a plain-text return the model can act on. Show results with widgets;
   publish rows as datasets so other agents can use them.
5. **Install into a host and try the examples.** Every example prompt on the
   manifest must route to this agent and produce a sensible answer:
   ```
   cd <plugboard host>
   uv add --group agents ../plugboard-<name>        # path now, git URL later
   echo 'PLUGBOARD_EXTRA_AGENTS=<package>' >> .env   # comma-separated if several
   uv run uvicorn project.asgi:application --port 8010
   uv run python tests/stream_smoke.py "<first example prompt>"
   ```
6. **Run the checklist** at the end of this file before calling it done.

## The contract

Read `reference.md` in this skill for the exact signatures. In short:

- **Imports.** `from plugboard import AgentManifest, register` and, in tools,
  `plugboard.turn.current_turn`, `plugboard.widgets.*`, `plugboard.artifacts.Dataset`,
  `plugboard.providers.providers`, `plugboard.registry.registry`. Never import
  another agent's package or anything under the host's `agents/`.
- **Register at import.** The host imports the package because it is named in
  `PLUGBOARD_EXTRA_AGENTS`; the import must call `register(AgentManifest(...))`
  at module level and do nothing else at import time (no network, no database).
- **Manifest fields that matter:**
  - `name`: short, snake_case; becomes `call_<name>`.
  - `title`: one or two words for the board ("Weather", "Root cause"). No
    "agent" suffix.
  - `routing_description`: written for the supervisor. Say what the agent
    answers, give the phrases a user would use, say what to pass in and what
    comes back, and say what it cannot do so the supervisor never offers it.
  - `persona`: written for the worker. Method in order, how to use each tool,
    what the user already sees (so the result text does not repeat it), what to
    do when something is missing, and to never invent data.
  - `tools`: a factory `make_tools() -> list[Callable]`, called once per turn.
  - `requires`: provider instance names the tools reach for (`["warehouse"]`,
    `["directory"]`, `["repos"]`: Database, Identity and Git providers by name).
    An agent whose providers are missing cannot be enabled; the board says why.
  - `config_schema`: JSON schema for settings; the console renders a form from
    it. Read settings at call time through `registry.get("<name>").settings`,
    never at factory time.
  - `examples`: two prompts written as a user would type them. They become
    quick starts in the UI and are the routing tests.
  - `source`: the repository URL, shown in the console.
  - `max_iters`: cap the loop. Four for a one-tool agent, eight if it explores.
- **Take capabilities before writing tools.** `plugboard.capabilities` has
  `database_tools(settings)` (list_tables, describe_table, run_sql over a Database
  provider), `identity_tools(settings)` (who_am_i, find_people, members_of over an
  Identity provider), `git_tools(settings)` (list_repositories, recent_commits,
  list_files, read_file over a Git provider) and `ask_user()`. List them on the manifest as `capabilities=[...]`; their
  tools join yours and their usage notes are appended to your persona, so do not
  repeat that method in the persona. Write a tool only for what no capability does.
- **Tools talk to the turn.** `turn = current_turn()` then:
  `turn.tool_call(name, args, summary)` once per call (the trail shows it),
  `turn.show(widget)` for a display widget, `turn.ask(QuestionWidget(...))` to
  block for an answer, `turn.artifacts.publish(Dataset(...))` to make rows
  available to other agents by id. Put the dataset id on the widget
  (`dataset_id=`) so the UI treats table and chart as views on the same thing.
- **Failure is a return value.** Catch what can fail (network, SQL, bad input),
  record it with `tool_call`, and return a sentence the model can act on.
  Never raise out of a tool for an expected failure.
- **Prefer a deterministic tool over a clever loop.** If the method is known,
  put it in code and let the model choose the inputs and narrate (see the
  host's ADR 13). Fewer, bigger tools beat many small ones.

## Giving the agent its own UI

Optional. Without it, the host renders the agent's datasets in its generic pane
(Data and SQL, Chart when drawn). With it, the agent's pane is yours.

1. `python .claude/skills/plugboard-agent/scripts/new_agent.py <name> --title "<Title>" --frontend`
   adds a `frontend/` Vite library build; or copy plugboard-weather's `frontend/`
   and rename. The build writes one ESM file into the package's `static/` directory.
2. React, ReactDOM and `@plugboard/sdk` are externals: never bundle them. The
   host's import map supplies its own instances, so there is one React.
3. Export `mount(el, ctx)` and `unmount(el)`. `ctx.component` names which of your
   components to render; for an `artifact` surface ctx also carries `artifact`,
   `dataset`, `conversationUuid`, `agentTitle` and `onClose`. Keep one root per
   element and make `mount` idempotent; the host re-mounts on context changes.
4. Import the SDK by group: `ui` (`Pane`, `TableView`, `SqlView`) so the pane matches
   the shell; `conversation` (`useDataset`, `runQuery`, `refresh`, `openArtifact`,
   `prefill`) to act on the conversation; `providers` to reach a connected system by
   name; `host.call` only when nothing above fits.
5. Style with `theme` tokens (`theme.ink`, `theme.muted`, `theme.line`, `theme.paper`,
   `theme.surface`, `theme.accent`, `theme.mono`), never a literal CSS variable. The
   host's Tailwind classes are not compiled for bundles.
6. On the manifest: `frontend=str(Path(__file__).parent / "static" / "<name>.js")`
   and `surfaces=[{"kind": "artifact", "component": "<Component>", "title": "..."}]`
   (or `"kind": "badge"` with `"key"` and `"icon"` for a header badge that opens a pane).
7. Commit the built file so a host needs no Node to use the agent.

## Checklist

- [ ] Package imports only `plugboard.*` and the standard library or its own dependencies.
- [ ] `register(AgentManifest(...))` runs at import; nothing else does.
- [ ] Routing description names the user phrases and what the agent cannot do.
- [ ] Persona says what the user already sees, so the result is a short summary.
- [ ] Every tool path calls `turn.tool_call` exactly once and returns text.
- [ ] Rows go out as a `Dataset`; the widget carries `dataset_id`.
- [ ] Settings are read at call time; `requires` lists every provider used.
- [ ] Shared behaviour (warehouse access, asking the user) comes from capabilities, not copied tools.
- [ ] Two `examples` on the manifest; both route to this agent in a host.
- [ ] `source` set; README says how to install into a host.
- [ ] `ruff check` clean at 99 columns.
- [ ] If there is a frontend: externals are react, react-dom, react/jsx-runtime, react-dom/client, @plugboard/sdk; the built file is committed; `surfaces` names the component.
